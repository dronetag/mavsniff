import io
import pcapng
import signal
import threading
import time

from pymavlink import mavutil

from mavsniff.utils.log import logger
from mavsniff.utils import ip


INTERFACE_MAGIC = 0x00000001
PACKET_MAGIC = 0x00000006
SECTION_MAGIC = 0x0A0D0D0A


class Replay:
    def __init__(self, device: mavutil.mavfile, file: io.BytesIO):
        self.file = file
        self.device = device
        self.done = False
        signal.signal(signal.SIGINT, self.stop)

    def run(self, limit=-1) -> int:
        """Replay a PCAPNG file to a device"""
        scanner = pcapng.FileScanner(self.file)
        # Resolution is handled in the mavlink library - timestamp is in seconds
        # resolution seems to be constant for all packets in a file
        # self.resolution_ts = interface_description.timestamp_resolution
        self.last_packet_ts = time.time()
        self.last_sent_ts = 0.0
        self.done = False
        written = 0
        empty = 0
        non_data = 0
        sleep_time = 0.0
        proceed = lambda: not self.done and (limit < 0 or written < limit)

        def report_stats():
            while proceed():
                logger.info(f"replayed {written}, empty: {empty}, unknown: {non_data}, slept: {sleep_time:.2}s")
                time.sleep(1.0)
        threading.Thread(target=report_stats).start()

        for packet in scanner:
            if self.done:
                break
            if packet is None:
                empty += 1
                continue
            if packet.magic_number != PACKET_MAGIC:
                non_data += 1
                continue
            if not packet.packet_data:
                empty += 1
                continue
            if packet.packet_data[0] in (0xfe, 0xfd): # mavlink magic bytes (0xfe "v1.0", 0xfd "v2.0")
                sleep_time += self._send_in_timely_manner(packet.timestamp, packet.packet_data)
            elif ip.is_packet(packet.packet_data):
                sleep_time += self._send_in_timely_manner(packet.timestamp, ip.get_payload(packet.packet_data))
            else:
                non_data += 1
                logger.debug(f"unknown packet: {packet.packet_data[:10]}...")
                continue
            written += 1
            if limit > 0 and written >= limit:
                break
        self.done = True
        return written

    def _send_in_timely_manner(self, timestamp: float, packet_data: bytes) -> float:
        """Replay a packet to the device"""
        packet_ts_delta: float = timestamp - self.last_packet_ts
        since_last_sent: float = time.time() - self.last_sent_ts
        sleep_time = (packet_ts_delta - since_last_sent)
        if sleep_time > 0.00001:
            time.sleep(sleep_time)
        self.device.write(packet_data)
        self.last_sent_ts = time.time()
        self.last_packet_ts = timestamp
        return sleep_time if sleep_time > 0.00001 else 0.0

    def stop(self, *args):
        self.done = True
