import click
import serial.tools.list_ports as list_ports


def ellipsis(message: str, maxlen: int):
    if len(message) > maxlen:
        return message[: maxlen - 3] + "..."
    return message


@click.command()
def ports():
    """List available serial ports"""
    click.echo("Usual baudrate is 115200, sometimes 57600")
    click.echo("Your available ports:")
    for port, desc, hwid in sorted(list_ports.comports()):
        click.echo(f" - {port}: {desc} [{ellipsis(hwid, 48)}]")
