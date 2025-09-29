import struct


## UDP header example
# 0x02, 0x00, 0x00, 0x00, # IP
# 0x45, # v4 + header length(1byte)
# 0x00, # DSCP + ECN
# 0x00, 0x39, # total length
# 0x55, 0x8d, 0x00, 0x00, # identification + fragment offset
# 0x80, 0x11, 0x00, 0x00, # ethertype(UDP) + flags + header checksum
# 0x7f, 0x00, 0x00, 0x01, # src IP
# 0x7f, 0x00, 0x00, 0x01, # dest IP
# 0x38, 0xd6, # src port
# 0x38, 0x6d, # dst port
def udp_header(seq: int, dl: int) -> bytes:
    """Create a UDP header for data-length dl and sequence number seq"""
    # fmt: off
    return bytes((
        0x02, 0x00, 0x00, 0x00, # IP
        0x45, # v4//1b + header length(20)//1b
        0x00, # DSCP + ECN
    )) + struct.pack('>HH', 20 + dl, seq) + bytes(( # total length
        0x00, 0x00, # fragment offset
        0x80, 0x11, 0x00, 0x00, # ethertype(UDP) + flags + header checksum
        0x7f, 0x00, 0x00, 0x01, # src IP
        0x7f, 0x00, 0x00, 0x01, # dest IP
        0x38, 0xd6, # src port
        0x38, 0x6d, # dst port
    )) + struct.pack('>HH', dl, 0) # length + checksum
    # fmt: on


def is_packet(packet: bytes) -> bool:
    """Check if a packet is an IP packet"""
    return packet[0:4] == b"\x02\x00\x00\x00" or packet[0:2] == b"\x01\x00"


def get_payload(packet: bytes) -> bytes:
    """Extract the user data (payload) from an IPv4 UDP or TCP packet."""
    # Check for possible Ethernet header (12 bytes) and skip it
    ip_header_start = 2
    if packet[0:4] == b"\x02\x00\x00\x00":
        ip_header_start += 2
    elif packet[0:2] != b"\x08\x00":
        if packet[12:14] == b"\x08\x00":
            ip_header_start += 12
    # IPv4 header length is in the lower 4 bits of byte 0 (after skipping 4 bytes of custom header)
    version_ihl = packet[ip_header_start]
    ihl = (version_ihl & 0x0F) * 4
    protocol = packet[ip_header_start + 9]
    l4_header_start = ip_header_start + ihl

    if protocol == 17:  # UDP
        l4_header_length = 8
    elif protocol == 6:  # TCP
        # TCP header length is in the upper 4 bits of the 12th byte of the TCP header (data offset)
        data_offset = (packet[l4_header_start + 12] >> 4) * 4
        l4_header_length = data_offset
    else:
        # Unknown protocol, return empty
        return b""

    payload_start = l4_header_start + l4_header_length
    return packet[payload_start:]
