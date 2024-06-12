# mavsniff

![Licence Badge](https://badgen.net/badge/License/MIT/blue)
![Coverage Badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/katomaso/bda1e64c276a6d6e6a4e65fb5dc9330b/raw/coverage.json)

Capture and replay MAVLink packets from your drone or GCS. Works on Linux and Windows.

You can read from a serial line (_/dev/ttyXXX or COMx_) or even from network (TCP and UDP). Mavsniff stores packets in pcapng format so you can analyse them with Wireshark.

## Instalation

```$ pip install mavsniff```

Mavsniff is distributed via PYPI and an entrypoint `mavsniff` should be available in your `$PATH` after installation.

## Usage

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
