import io
import os
import signal
import struct
import threading
import time
from typing import Any, Optional

import pcapng
import serial
from pymavlink import mavutil
from pymavlink.generator import mavparse

from mavsniff.utils.ip import udp_header
from mavsniff.utils.log import logger


class Capture:
    """Capture reads Mavlink messages from a device and store them into a PCAPNG file"""

    file: io.BufferedWriter
    device: mavutil.mavfile
    writer: Optional[pcapng.FileWriter]
    done: bool
    sbh: pcapng.blocks.SectionHeader

    def __init__(self, device: mavutil.mavfile, file: io.BufferedWriter):
        self.device = device
        self.file = file
        self.done = False
        self.writer = None

        self.received = 0
        self.parse_errors = 0
        self.empty_messages = 0
        self.bad_messages = 0
        self.other_messages = 0

        self.sbh = pcapng.blocks.SectionHeader(
            msgid=0,
            endianness="<",
            options={
                "shb_userappl": "mavsniff",
            },
        )
        self.sbh.register_interface(
            pcapng.blocks.InterfaceDescription(
                msdgid=0x01,
                endianness="<",
                interface_id=0x00,
                section=self.sbh,
                options={
                    "if_name": device.address
                    if ":" not in device.address
                    else device.address.split(":")[1],
                    "if_txspeed": getattr(self.device, "baudrate", 0),
                    "if_rxspeed": getattr(self.device, "baudrate", 0),
                    "if_tsresol": struct.pack("<B", 6),  # negative power of 10
                    # should we deal with timestamp resolution?
                },
            )
        )

    def stop(self, sig: int, frame: Optional[Any]) -> None:
        logger.info("Termination event caught - quitting")
        self.done = True

    def report_stats(self):
        while not self.done:
            logger.info(
                f"captured {self.received}, not-parsed: {self.other_messages}, "
                f"empty: {self.empty_messages}/s, bad: {self.bad_messages}"
            )
            self.empty_messages = 0  # zero-out the empty messages counter or it overflows quickly
            time.sleep(1.0)

    def run(self, limit: int = -1, limit_invalid_packets: int = -1) -> int:
        """Store Mavlink messages into a PCAPNG file"""
        if self.writer is not None:
            raise RuntimeError("Called run method twice")

        signal.signal(signal.SIGINT, self.stop)
        if os.name == "posix":
            signal.signal(signal.SIGKILL, self.stop)
            signal.signal(signal.SIGHUP, self.stop)

        self.writer = pcapng.FileWriter(self.file, self.sbh)
        self.done = False

        threading.Thread(target=self.report_stats).start()

        while not self.done:
            try:
                msg = self.device.recv_msg()
                self.parse_errors = 0
                if msg is None:
                    self.empty_messages += 1
                    continue
                if msg.get_type() == "BAD_DATA":
                    self.bad_messages += 1
                    continue
                self.received += 1
                self._write_packet(self.received, msg.pack(self.device.mav))
                if limit > 0 and self.received >= limit:
                    break
            except mavparse.MAVParseError:
                self.parse_errors += 1
                self.other_messages += 1
                if limit_invalid_packets > 0 and self.parse_errors > limit_invalid_packets:
                    raise RuntimeError("Too many invalid packets in a row")
                continue
            except serial.SerialException:
                logger.info("serial line closed")
                break
        self.device.close()
        return self.received

    def _write_packet(self, seq: int, data: bytes):
        """Write packet to the device"""
        assert self.writer is not None
        now_us = time.time_ns() // 1000
        payload = udp_header(seq, len(data)) + data
        self.writer.write_block(
            pcapng.blocks.EnhancedPacket(
                section=self.sbh,
                interface_id=0x00,
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
            )
        )
