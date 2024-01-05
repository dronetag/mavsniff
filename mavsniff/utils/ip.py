import struct

## UDP header example
# 0x02, 0x00, 0x00, 0x00, # IP
# 0x45, # v4 + header length(1byte)
# 0x00, # DSCP + ECN
# 0x00, 0x39, # total length
# 0x55, 0x8d, 0x00, 0x00, # identification + fragment offser
# 0x80, 0x11, 0x00, 0x00, # ethertype(UDP) + flags + header checksum
# 0x7f, 0x00, 0x00, 0x01, # src IP
# 0x7f, 0x00, 0x00, 0x01, # dest IP
# 0x38, 0xd6, # src port
# 0x38, 0x6d, # dst port
def udp_header(seq: int, dl: int) -> bytes:
    """Create a UDP header for data-length dl and sequence number seq"""
    return bytes((
        0x02, 0x00, 0x00, 0x00, # IP
        0x45, # v4//1b + header length(20)//1b
        0x00, # DSCP + ECN
    )) + struct.pack(">HH", 20 + dl, seq) + bytes(( # total length
        0x00, 0x00, # fragment offser
        0x80, 0x11, 0x00, 0x00, # ethertype(UDP) + flags + header checksum
        0x7f, 0x00, 0x00, 0x01, # src IP
        0x7f, 0x00, 0x00, 0x01, # dest IP
        0x38, 0xd6, # src port
        0x38, 0x6d, # dst port
    )) + struct.pack('>HH', dl, 0) # length + checksum


def is_packet(packet: bytes) -> bool:
    """Check if a packet is an IP packet"""
    return packet[0:4] == b"\x02\x00\x00\x00"


def get_payload(packet: bytes) -> bytes:
    """Get the data from a UDP packet"""
    b = struct.unpack(">c", packet[4:5])[0]
    hl = (b[0] & 0x0f) * 4
    # add UDP or TCP header length
    hl += 8 # hard-code UDP header length
    return packet[hl+4:]
