# mavsniff

![License Badge](https://badgen.net/badge/License/MIT/blue)
![Coverage Badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/katomaso/bda1e64c276a6d6e6a4e65fb5dc9330b/raw/coverage.json)

Capture and replay MAVLink packets from your drone or GCS. Works on Linux and Windows.

You can read from a serial line (_/dev/ttyXXX or COMx_) or even from network (TCP and UDP). Mavsniff stores packets in pcapng format so you can analyze them with Wireshark.

## Installation

```pip install git+https://github.com/dronetag/mavsniff.git@v1.1.2```

If you are running mavsniff on WSL then you need a tool for forwarding the USB to Linux.
For that, WSL uses _usbip_ on Linux side `sudo apt install usbip`
and [WSL USB Manager](https://gitlab.com/alelec/wsl-usb-gui/-/releases) on Windows side.

For installation on Windows, you will need Python3 (install from Windows Store) and Git
(install from https://git-scm.com/).


## Usage

Once your device is plugged then we need to find out on which port did it connect. It
will be /dev/ttyACMx (or /dev/ttyUSBx) on Linux and COMxy on Windows. Use `mavsniff ports`
for this.

```
$ mavsniff ports
Usual baudrate is 115200, sometimes 57600
Your available COM ports are:
 - /dev/ttyACM0: Dronetag Beacon 2 [USB VID:PID=1900:5212 SER=397E9D237C782B7B LO...]
```

on Windows, the output might be more cryptic but still only one COM port shows up and
that would be your device (COMxy)

```
Your available COM ports are:
 - COM67: USB Serial Device (COM67) [USB VID:PID=1900:5212 SER=397E9D237C782B7B LO...]
```

Now you are ready to to capture or replay traffic.

```bash
$ mavsniff capture --device udp://localhost:5467 --file recording --mavlink-dialect path-to-custom/my-dialect.xml
$ mavsniff replay -f recording -d /dev/ttyS0 -m my-dialect --baud=57600 # for serial line, specify baud if different from 115200
$ mavsniff ports # show available serial ports
$ mavsniff wsplugin # install Wireshark MAVlink disector plugin for reading Mavlink packets
```

### Devices

 * `-d /dev/ttyS0` - standard serial port on UNIX systems
 * `-d COMx` - from COM1 to COM8 - standard serial ports on Windows systems
 * `-d udp://<host>:<port>` or `tcp://<host>:<port>` - receive or send packets over network (TCP or UDP)
 * `-d file.tlog` - almost any (at least a bit standard) binary or textual file can be replayed

### Dialects

Default dialect is **arduinomega** and version is **2.0**. You can specify your custom dialect in form
of mavlink's XML definition via `--mavlink-dialect/-m` flag. Mavsniff will copy your XML into internal
pymavlink folder and compile it on the first run. All subsequent runs won't update nor recompile your
dialect. Once your custom dialect was imported and compiled, you can reference by its name (XML filename
without extension).


### Using with network

mavsniff uses compatible format of UDP packets with QGroundControl. That means if you capture packets
emitted (mirrored) by QGroundControl with Wireshark then you will be able to replay those to any serial
device. Those packets have minimal ethernet header `02 00 00 00` and uses 20 bytes long IP header and
only 8 bytes for a UDP header. Any other packets will not be replayable by mavsniff.


## Developement

Start developing by cloning the repo and installing tha application locally

```bash
$ git clone git@github.com:katomaso/mavsniff.git && cd mavsniff
$ python -m venv .venv && source $VENV
$ pip install poetry
$ poetry install -E dev
$ poetry run pytest
```
