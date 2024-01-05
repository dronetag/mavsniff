import click
import serial.tools.list_ports as list_ports


def elipsis(string, length):
    if len(string) > length:
        return string[:length - 3] + "..."
    return string


@click.command()
def ports():
    """List available serial ports"""
    click.echo("Usual baudrated are 57600, 115200")
    click.echo("Your available COM ports are:")
    for port, desc, hwid in sorted(list_ports.comports()):
        click.echo(f" - {port}: {desc} [{elipsis(hwid, 48)}]")
