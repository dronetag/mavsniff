from pymavlink import mavutil
from pymavlink.generator import mavparse

from .log import logger

ParseError = mavparse.MAVParseError

# HACK: fixup - do not fill RAM with mavlink messages when sniffing
mavutil.add_message = lambda messages, mtype, msg: None

def mavlink(uri:str, input:bool, version:int=2, dialect:str=None, **kwargs) -> mavutil.mavfile:
    """
    Create mavlink IO device
    @param uri: device path (e.g. udp://localhost:14445, tcp://localhost:14550, /dev/ttyUSB0, /dev/ttyS0, COM1...)
    @param dialect: MAVLink dialect (all, ardupilotmega, common, pixhawk...) @see pymavlink.dialects for more
    """
    if input: # the names for input and output are not consistent in pymavlink
        if uri.startswith("tcp:"):
            uri = "tcpin:" + uri[6:]
        if uri.startswith("udp:"):
            uri = "udpin:" + uri[4:]
    else:
        if uri.startswith("tcpout:"):
            uri = "tcp:" + uri[4:]
        if uri.startswith("udp:"):
            uri = "udpout:" + uri[4:]

    if "://" in uri: # allow people to write URL-like paths
        uri = ":".join(uri.split("://", 1)) # pymavlink expects `udp:localhost:14550` instead of `udp://localhost:14550`

    logger.debug(f"creating mavlink device: {uri}")
    m = mavutil.mavlink_connection(uri, input=input, dialect=dialect, **clean(kwargs))
    if m is None:
        return None


def clean(kwargs:dict) -> dict:
    """Remove None values from a dictionary"""
    return {k: v for k, v in kwargs.items() if v is not None}