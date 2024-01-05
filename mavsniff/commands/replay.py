import click
import logging

from mavsniff.utils.log import logger
from mavsniff.utils.mav import mavlink
from mavsniff.replay import Replay

as_pcapng = lambda f: f if "." in f else f + ".pcapng"

@click.command()
@click.option("--file", "-f", required=True, help="pcap file to read from")
@click.option("--device", "-d", required=True, help="device URI (/dev/tty..., COMx on windows or udp://host:port, tcp://host:port)")
@click.option("--limit", "-l", default=-1, type=int, help="limit the number of read/written packets (default -1 unlimited)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
def replay(file, device, verbose, limit) -> int:
    """Replay mavlink communication from a pcapng file to a (serial emulating) device"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    pcapfile = None
    try:
        pcapfile = open(as_pcapng(file), "rb")
    except Exception as e:
        logger.error(f"Failed to open file {file}: {e}")
        return 1

    mavconn = None
    try:
        mavconn = mavlink(device, input=True)
    except Exception as e:
        pcapfile.close()
        logger.error(f"Failed to open file {file}: {e}")
        return 1

    try:
        replayed = Replay(file=pcapfile, device=mavconn).run(limit=limit)
        logger.info(f"replayed {replayed} valid MAVLink packets")
        return 0
    finally:
        pcapfile.close()
        mavconn.close()