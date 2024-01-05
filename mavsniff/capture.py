import io
import pcapng
import serial
import time
import struct

import signal
import time
import threading

from pymavlink import mavutil
from pymavlink.generator import mavparse

from mavsniff.utils.log import logger
from mavsniff.utils.ip import udp_header


class Capture:
    """Capture reads Mavlink messages from a device and store them into a PCAPNG file"""

    def __init__(self, device: mavutil.mavfile, file: io.BytesIO):
        self.device = device
        self.file = file
        self.interface_id=0x00
        self.done = False
        self.sbh = pcapng.blocks.SectionHeader(msgid=0, endianness="<", options={
            'shb_userappl': 'mavsniff',
        })
        self.sbh.register_interface(pcapng.blocks.InterfaceDescription(msdgid=0x01, endianness="<", interface_id=self.interface_id, section=self.sbh, options={
            'if_name': device.address if ":" not in device.address else device.address.split(":")[1],
            'if_txspeed': getattr(self.device, "baudrate", 0),
            'if_rxspeed': getattr(self.device, "baudrate", 0),
            'if_tsresol': struct.pack('<B', 6), # negative power of 10
            # should we deal with timestamp resolution?
        }))
        signal.signal(signal.SIGINT, self.stop)

    def run(self, limit=-1, limit_invalid_packets=-1) -> dict:
        """Store Mavlink messages into a PCAPNG file"""
        self.writer = pcapng.FileWriter(self.file, self.sbh)
        self.done = False
        received = 0
        parse_errors = 0
        empty_messages = 0
        bad_messages = 0
        other_messages = 0

        def report_stats():
            while not self.done:
                logger.info(f"captured {received}, not-parsed: {other_messages}, empty: {empty_messages}, bad: {bad_messages}")
                time.sleep(1.0)
        threading.Thread(target=report_stats).start()

        while not self.done:
            try:
                msg = self.device.recv_msg()
                parse_errors = 0
                if msg is None:
                    empty_messages += 1
                    continue
                if msg.get_type() == 'BAD_DATA':
                    bad_messages += 1
                    continue
                received += 1
                self._write_packet(received, msg.pack(self.device.mav))
                if limit > 0 and received >= limit:
                    break
            except mavparse.MAVParseError:
                parse_errors += 1
                other_messages += 1
                if limit_invalid_packets > 0 and parse_errors > limit_invalid_packets:
                    raise RuntimeError("Too many invalid packets in a row")
                continue
            except serial.SerialException:
                logger.info("serial line closed")
                break
        return received

    def _write_packet(self, seq:int, data: bytes):
        """Write packet to the device"""
        now_us = time.time_ns() // 1000
        payload = udp_header(seq, len(data)) + data
        self.writer.write_block(pcapng.blocks.EnhancedPacket(
            section=self.sbh,
            interface_id=self.interface_id,
            packet_data=payload,
            timestamp_high=(now_us & 0xFFFFFFFF00000000) >> 32,
            timestamp_low=(now_us & 0xFFFFFFFF),
            captured_len=len(payload),
            packet_len=len(payload),
            endianness="<",
            # options={
            #     'epb_flags': 0,
            #     'epb_tsresol': 6, # negative power of 10
            #     'epb_tsoffset': 0,
            #     'epb_len': len(packet_bytes),
            # },
        ))

    def stop(self, *args):
        self.done = True
