import logging
import signal
import sys

import click

from mavsniff.capture import Capture
from mavsniff.utils.log import logger
from mavsniff.utils.mav import mavlink


def as_pcapng(filename: str):
    """Append .pcapng suffix if there is no suffix in the filename"""
    return filename if "." in filename else filename + ".pcapng"


@click.command()
@click.option("--file", "-f", required=True, help="pcap file to save the communication to")
@click.option(
    "--device",
    "-d",
    required=True,
    help="device URI (/dev/tty..., COMx on windows or udp://host:port, tcp://host:port))",
)
@click.option(
    "--limit",
    "-l",
    default=-1,
    type=int,
    help="limit the number of read/written packets (default -1 unlimited)",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
@click.option(
    "--mavlink-dialect", "-m", help="Mavlink dialect (see pymavlink.dialects for possible values)"
)
@click.option(
    "--mavlink-version",
    "-n",
    type=int,
    default=2,
    help="Set mavlink protocol version (options: 1,2; default: 2)",
)
@click.option("--baud", "-b", type=int, help="Serial communication baud rate")
def capture(
    device: str,
    file: str,
    limit: int,
    verbose: bool,
    mavlink_version: int,
    mavlink_dialect: str,
    **kwargs,
):
    """Capture mavlink communication from a serial device and store it into a pcapng file"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    pcapfile = None
    try:
        pcapfile = open(as_pcapng(file), "wb")
    except Exception as e:
        if verbose:
            logger.exception(e)
        else:
            logger.error(f"Failed to open file {file}: {e}")
        return 1

    mavconn = None
    try:
        mavconn = mavlink(
            device, input=True, version=mavlink_version, dialect=mavlink_dialect, **kwargs
        )
    except Exception as e:
        pcapfile.close()
        if verbose:
            logger.exception(e)
        else:
            logger.error(str(e))
        return 1

    capture = Capture(device=mavconn, file=pcapfile)
    signal.signal(signal.SIGINT, capture.stop)

    try:
        if limit < 0:
            print("Capturing without packets limit - use ctrl+c to stop", file=sys.stderr)
        captured = capture.run(limit=limit)
        logger.info(f"captured {captured} valid MAVLink packets")
        return 0
    finally:
        pcapfile.close()
        mavconn.close()
