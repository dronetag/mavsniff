import io
import pcapng
import time
import threading

from pymavlink import mavutil
from pymavlink.dialects.v20 import ardupilotmega as mavlink2

from mavsniff.utils.mav import mavlink
from mavsniff.utils import ip
from mavsniff.capture import Capture
from mavsniff.replay import Replay

TEST_DEVICE_URL = "tcp://localhost:3728"

def _generate_packets():
    mavconn = mavlink(TEST_DEVICE_URL, input=False)
    try:
        for seq in range(1, 5):
            if seq % 2 == 0:
                mavconn.set_mode_manual()
            else:
                mavconn.set_mode_loiter()
            time.sleep(0.1)
    finally:
        mavconn.close()

def test_capture_timing():
    """Simple test that packets get captured with correct timing"""
    buffer = io.BytesIO()
    mavconn = mavlink(TEST_DEVICE_URL, input=True)

    # step 1: generate packets with pauses between them and save those into a in-memory pcapng file."""
    ## start reading thread that blocks while waiting for IO
    try:
        c = Capture(device=mavconn, file=buffer)
        t = threading.Thread(target=c.run)
        t.start(); time.sleep(0.01)

        ## start generating packets
        _generate_packets()
        c.stop()
        t.join()
        mavlink_parser = mavconn.mav
        mavlink_parser.robust_parsing = True
    finally:
        mavconn.close()

    # step 2: read the in-memory file and check that the timing of packets is saved correctly
    buffer.seek(0)
    packets = list(pcapng.FileScanner(buffer))

    assert len(packets) == 2+4 # 2 section headers, 4 packets
    assert isinstance(packets[0], pcapng.blocks.SectionHeader)
    assert isinstance(packets[1], pcapng.blocks.InterfaceDescription)
    assert isinstance(packets[2], pcapng.blocks.EnhancedPacket)

    packet_data = ip.get_payload(packets[2].packet_data)

    try:
        msg = mavlink_parser.parse_char(packet_data)
        assert msg is not None, "packet is not a mavlink message"
        assert msg.get_type() != "BAD_DATA", "packet is not a valid mavlink"
    except Exception as e:
        assert False, f"failed to parse packet: {packet_data[:10]}... {e}"

    assert 0.15 > (packets[3].timestamp - packets[2].timestamp) > 0.08
    assert 0.15 > (packets[4].timestamp - packets[3].timestamp) > 0.08
    assert 0.15 > (packets[5].timestamp - packets[4].timestamp) > 0.08


def test_capture_replay():
    """Test full circle - capture packets into a pcapng file and then replay them back."""
    messages = []
    times = []

    # step 1: start a listening thread that blocks
    file = open("test_capture_replay.pcapng", 'wb')
    mavinput = mavlink(TEST_DEVICE_URL, input=True)
    c = Capture(mavinput, file)
    try:
        t = threading.Thread(target=c.run)
        t.start(); time.sleep(0.01)
        _generate_packets()
    finally:
        c.stop()
        t.join()
        file.close()
        mavinput.close()

    # step 3: read the in-memory file and check that the timing of packets is saved correctly
    mavinput = mavlink(TEST_DEVICE_URL, input=True)
    done = False
    def read_messages():
        start_time = time.time()
        while not done:
            try:
                msg = mavinput.recv_msg()
                if msg is None:
                    continue
                now = time.time()
                messages.append(msg)
                times.append(now - start_time)
                start_time = now
            except Exception as e:
                print(e)
                break

    try:
        mavfile = mavlink(TEST_DEVICE_URL, input=False, autoreconnect=True)
        t = threading.Thread(target=read_messages); t.start(); time.sleep(0.01)
        try:
            file = open("test_capture_replay.pcapng", 'rb')
            Replay(file=file, device=mavfile).run()
        finally:
            mavfile.close()
            file.close()
    finally:
        done = True
        mavinput.close()
        t.join()

    assert len(messages) == 4
    assert all(1.15 > t > 0.08 for t in times[1:])


def test_capture_garbage():
    """Simple test that packets get captured with correct timing"""
    device = mavlink(TEST_DEVICE_URL, input=True, dialect="ardupilotmega")
    buffer = io.BytesIO()

    # step 1: generate packets with pauses between them and save those into a in-memory pcapng file."""
    ## start reading thread that blocks while waiting for IO
    c = Capture(device, buffer)
    t = threading.Thread(target=c.run)
    t.start(); time.sleep(0.01)

    ## start generating packets
    _generate_packets_and_garbage(mavlink(TEST_DEVICE_URL, input=False, dialect="ardupilotmega"))
    c.stop()
    t.join()

    # step 2: read the in-memory file and check that the timing of packets is saved correctly
    buffer.seek(0)
    packets = list(pcapng.FileScanner(buffer))

    # assert len(packets) == 2+4 # 2 section headers, 4 packets
    assert isinstance(packets[0], pcapng.blocks.SectionHeader)
    assert isinstance(packets[1], pcapng.blocks.InterfaceDescription)
    assert isinstance(packets[2], pcapng.blocks.EnhancedPacket)
    msg_count13 = device.mav.parse_char(ip.get_payload(packets[2].packet_data))
    assert isinstance(msg_count13, mavlink2.MAVLink_mission_count_message), f"should be Count(13) but is {msg_count13.get_type()}"
    assert msg_count13.count == 13, "the count should be 13"
    msg_count42 = device.mav.parse_char(ip.get_payload(packets[3].packet_data))
    assert isinstance(msg_count42, mavlink2.MAVLink_mission_count_message), f"should be Count(42) but is {msg_count42.get_type()}"
    assert msg_count42.count == 42, "the count should be 42"
    msg_count50 = device.mav.parse_char(ip.get_payload(packets[4].packet_data))
    assert isinstance(msg_count50, mavlink2.MAVLink_mission_count_message), f"should be Count(50) but is {msg_count50.get_type()}"
    assert msg_count50.count == 50, "the count should be 50"
    msg_count51 = device.mav.parse_char(ip.get_payload(packets[5].packet_data))
    assert isinstance(msg_count51, mavlink2.MAVLink_mission_count_message), f"should be Count(51) but is {msg_count51.get_type()}"
    assert msg_count51.count == 51, "the count should be 51"


def _generate_packets_and_garbage(mavlink: mavutil.mavfile):
    mavlink.write(b'garbage')
    mavlink.write(mavlink2.MAVLink_mission_count_message(target_system=42, target_component=0, count=13).pack(mavlink.mav))
    time.sleep(0.1)
    mavlink.write(mavlink2.MAVLink_mission_count_message(target_system=42, target_component=0, count=42).pack(mavlink.mav))
    invalid_message = bytearray(mavlink2.MAVLink_mission_count_message(target_system=42, target_component=0, count=43).pack(mavlink.mav))
    for i in range(0, 11): invalid_message[i] = 0x00 # zero the mavlink header to render it invalid
    mavlink.write(invalid_message)
    mavlink.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    time.sleep(0.1)
    mavlink.write(mavlink2.MAVLink_mission_count_message(target_system=42, target_component=0, count=50).pack(mavlink.mav))
    time.sleep(0.1)
    mavlink.write(mavlink2.MAVLink_mission_count_message(target_system=42, target_component=0, count=51).pack(mavlink.mav))
    time.sleep(0.1)
    mavlink.close()
