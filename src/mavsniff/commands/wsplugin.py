"""
Build and install Mavlink plugin for Wireshark

Effectivelly, this command is a wrapper around pymavlink's mavgen tool, which generates a Wireshark
plugin from Mavlink XML definitions as following:

python3 -m pymavlink.tools.mavgen --lang=WLua --wire-protocol=2.0 \
    --output=mavlink_2_common message_definitions/v1.0/common.xml

Filter expression to use in Wireshark to see only Mavlink traffic is as following:
mavlink_proto && not icmp
"""

import os.path
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import click
import pymavlink
from pymavlink.generator import mavgen, mavparse

from mavsniff.utils import mav

WIN_PATH = "%APPDATA%\\Wireshark\\plugins"
LIN_PATH = "~/.local/lib/wireshark/plugins"
OSX_PATH = "%APPDIR%/Contents/PlugIns/wireshark"

VERSIONS = (mavparse.PROTOCOL_0_9, mavparse.PROTOCOL_1_0, mavparse.PROTOCOL_2_0)


@click.command()
@click.option("--wireshark-plugin-dir", default=None, help="Wireshark plugin directory")
@click.option("--override", is_flag=True, default=False, help="Replace existing plugin")
@click.option("--delete", is_flag=True, default=False, help="Delete existing plugin")
@click.option(
    "--version",
    "-m",
    default=mavgen.DEFAULT_WIRE_PROTOCOL,
    show_default=True,
    help="Mavlink version; choices: " + str(VERSIONS),
)
@click.argument("dialects", nargs=-1)
def wsplugin(
    dialects: Iterable[str],
    version: str,
    wireshark_plugin_dir: Optional[str],
    override: bool,
    delete: bool,
) -> int:
    """Build and install Mavlink plugin for Wireshark"""
    if version not in VERSIONS:
        click.echo(f"[ERROR] Invalid mavlink version: {version}")
        return 1

    plugin_name = "mavlink_disector.lua"
    if wireshark_plugin_dir is None:
        wireshark_plugin_path = Path(click.get_app_dir("wireshark"), "plugins").expanduser()
        if wireshark_plugin_path.exists():
            wireshark_plugin_dir = str(wireshark_plugin_path)

    if wireshark_plugin_dir is None:
        if sys.platform == "win32":
            wireshark_plugin_dir = os.path.expandvars(WIN_PATH)
        elif sys.platform == "darwin":
            wireshark_plugin_dir = os.path.expandvars(OSX_PATH)
        else:
            wireshark_plugin_dir = os.path.expandvars(LIN_PATH)
    click.echo(f"[INFO] Using wireshark plugin directory: {wireshark_plugin_dir}")

    wireshark_plugin_path = Path(wireshark_plugin_dir).expanduser()
    if not wireshark_plugin_path.exists():
        wireshark_plugin_path.mkdir(parents=True, exist_ok=True)

    plugin_file = wireshark_plugin_path / plugin_name
    version_file = plugin_file.parent / "mavlink_disector_plugin.version"

    if delete:
        if plugin_file.exists():
            plugin_file.unlink()
        if version_file.exists():
            version_file.unlink()
        click.echo(f"[INFO] Deleted {plugin_file}")
        return 0

    if not dialects:
        dialects = ("ardupilotmega",)
        click.echo(f"[INFO] No dialects specified, using: {dialects}")
        click.echo(f"[INFO] Available dialects: {mav.list_dialects(version)}")

    if plugin_file.exists() and not override:
        click.echo(f"[INFO] Found existing {plugin_file}")
        if version_file.exists():
            click.echo(version_file.read_text())
        click.echo("[ERROR] Use --override to overwrite it")
        return 1

    opts = mavgen.Opts(str(plugin_file), wire_protocol=version, language="wlua")
    mavgen.mavgen(
        opts,
        (
            Path(mavgen.__file__).parent / f"../message_definitions/v1.0/{dialect}.xml"
            for dialect in dialects
        ),
    )

    if not plugin_file.exists():
        click.echo(f"[ERROR] Did not write {plugin_file} correctly")
        return 1

    version_file.write_text(
        f"""Pymavlink version: {getattr(pymavlink, '__version__', 'too-new')}
Built at: {datetime.now()}
Dialects: {dialects}
"""
    )
    return 0
