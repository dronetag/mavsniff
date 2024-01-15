import os
import sys
from pathlib import Path

from pymavlink import mavutil
from pymavlink.generator import mavgen, mavparse

from .log import logger

ParseError = mavparse.MAVParseError

# HACK: fixup - do not fill RAM with mavlink messages when sniffing
mavutil.add_message = lambda messages, mtype, msg: None


def mavlink(uri: str, input: bool, dialect: str = "ardupilotmega", version: int = 2, **kwargs) -> mavutil.mavfile:
    """
    Create mavlink IO device
    @param uri: device path (e.g. udp://localhost:14445, tcp://localhost:14550, /dev/ttyUSB0, /dev/ttyS0, COM1...)
    @param dialect: MAVLink dialect (all, ardupilotmega, common, pixhawk...) @see pymavlink.dialects for more
    """
    if input:  # the names for input and output are not consistent in pymavlink
        if uri.startswith("tcp:"):
            uri = "tcpin:" + uri[6:]
        if uri.startswith("udp:"):
            uri = "udpin:" + uri[4:]
    else:
        if uri.startswith("tcpout:"):
            uri = "tcp:" + uri[4:]
        if uri.startswith("udp:"):
            uri = "udpout:" + uri[4:]

    # we allow people to write URL-like paths but pymavlink expects
    # `udp:localhost:14550` instead of `udp://localhost:14550`
    if "://" in uri:
        uri = ":".join(uri.split("://", 1))

    dialect = check_or_install_dialect(dialect, version)

    logger.debug(f"setting dialect {dialect} and version {version}")
    if version == 2:
        # mavutil.set_dialect uses only existence of this env var to determine the version
        os.environ["MAVLINK20"] = "yez"
    else:
        del os.environ["MAVLINK20"]
    mavutil.set_dialect(dialect)

    logger.debug(f"creating mavlink device: {uri}")
    m = mavutil.mavlink_connection(uri, input=input, dialect=dialect, **clean(kwargs))
    if m is None:
        raise RuntimeError(f"failed to create mavlink device: {uri}")
    return m


def clean(kwargs: dict) -> dict:
    """Remove None values from a dictionary"""
    return {k: v for k, v in kwargs.items() if v is not None}


def check_or_install_dialect(dialect: str, version: int) -> str:
    """Check if a dialect is installed, if not try to install it"""
    if dialect is None:
        return "ardupilotmega"

    if dialect.endswith(".xml") and Path(dialect).exists():
        try:
            xml_path = install_dialect(dialect, version)
            dialect = build_dialect(xml_path)
        except:
            xml_path.unlink()
            raise

    available_dialects = list_dialects(version)
    if dialect not in available_dialects:
        raise RuntimeError(f'Unknown dialect "{dialect}", available dialects: {available_dialects}')
    return dialect


def install_dialect(dialect: str, version: int) -> Path:
    """Install dialect XML definition into Pymavlink's internal directory"""
    dialect_path = Path(dialect)
    mavlink_root = Path(mavgen.__file__).parent.parent
    dialect_root_dir = mavlink_root / "dialects" / ("v20" if version == 2 else "v10")
    if dialect_path.parent == dialect_root_dir:
        raise RuntimeError(
            "Do not specify dialect as a full path to pymavlink's " "internal directory. Use alias (name) instead."
        )

    # install XML definition and build a python module from it
    dialect_target_path = dialect_root_dir / dialect_path.name
    logger.debug(f"installing dialect {dialect} into {dialect_target_path}")
    if dialect_target_path.exists():
        logger.warn(f"dialect {dialect_target_path} already installed")
        return dialect_target_path

    dialect_target_path.write_bytes(dialect_path.read_bytes())
    return dialect_target_path


def build_dialect(xml_path: Path) -> str:
    """Build a python module from a dialect XML definition inside pymavlink's internal directory"""
    if not xml_path or not xml_path.exists():
        raise RuntimeError(f"XML definition for dialect {xml_path.stem} not found at {xml_path}")

    py_path = xml_path.with_suffix(".py")
    if py_path.exists():
        logger.warn(f"dialect {py_path.stem} already built")
        return py_path.stem

    installed = mavgen.mavgen_python_dialect(
        py_path.stem,
        wire_protocol=mavparse.PROTOCOL_2_0 if "v20" in str(xml_path) else mavparse.PROTOCOL_1_0,
        with_type_annotations=sys.version_info.major == 3,
    )

    if not installed:
        raise RuntimeError(f"Failed to install (compile) dialect {py_path.stem}")
    return py_path.stem


def list_dialects(version: int) -> list:
    """List all installed dialects"""
    mavlink_root = Path(mavgen.__file__).parent.parent
    dialect_root_dir = mavlink_root / "dialects" / ("v20" if version == 2 else "v10")
    return [d.stem for d in dialect_root_dir.glob("*.py") if d.stem != "__init__"]
