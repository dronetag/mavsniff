import click
import logging

from mavsniff.utils.log import logger
from mavsniff.utils.mav import mavlink
from mavsniff.capture import Capture


as_pcapng = lambda f: f if "." in f else f + ".pcapng"

@click.command()
@click.option("--file", "-f", required=True, help="pcap file to save the communication to")
@click.option("--device", "-d", required=True, help="device URI (/dev/tty..., COMx on windows or udp://host:port, tcp://host:port))")
@click.option("--limit", "-l", default=-1, type=int, help="limit the number of read/written packets (default -1 unlimited)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
@click.option("--mavlink-version", "-m", type=int, default=2, help="Set mavlink protocol version (options: 1,2; default: 2)")
@click.option("--mavlink-dialect", "-n", help="Mavlink dialect (see pymavlink.dialects for possible values)")
@click.option("--baud", "-b", type=int, help="Serial communication baud rate")
def capture(device:str, file:str, limit:int, verbose:bool, mavlink_version:int, mavlink_dialect:str, **kwargs):
    """Capture mavlink communication from a serial device and store it into a pcapng file"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    pcapfile = None
    try:
        pcapfile = open(as_pcapng(file), "wb")
    except Exception as e:
        logger.error(f"Failed to open file {file}: {e}")
        return 1

    mavconn = None
    try:
        mavconn = mavlink(device, input=True, version=mavlink_version, dialect=mavlink_dialect, **kwargs)
    except Exception as e:
        file.close()
        logger.error(f"Failed to open file {file}: {e}")
        return 1

    try:
        captured = Capture(device=mavconn, file=pcapfile).run(limit=limit)
        logger.info(f"captured {captured} valid MAVLink packets")
        return 0
    finally:
        pcapfile.close()
        mavconn.close()
