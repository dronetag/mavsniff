import click
import sys

from .commands import capture, ports, replay, wsplugin

@click.group()
def main():
    pass

main.add_command(capture.capture)
main.add_command(replay.replay)
main.add_command(wsplugin.wsplugin)
main.add_command(ports.ports)

sys.exit(main())