# mavsniff

Capture and replay MAVLink packets from your drone or GCS. Works on Linux and Windows.

You can read from a serial line (_/dev/ttyXXX or COMx_) or even from network (TCP and UDP). Mavsniff stores packets in pcapng format so you can analyse them with Wireshark.

## Instalation

```$ pip install mavsniff```

Mavsniff is distributed via PYPI and an entrypoint `mavsniff` should be available in your `$PATH` after installation.

## Usage

```bash
$ mavsniff capture --device udp://localhost:5467 --file recording  # will append .pcapng to the file name autom7y
$ mavsniff replay -f recording -d /dev/ttyS0 --baud=57600 # for serial line, specify baud if different from 115200
$ mavsniff ports # show available serial ports
$ mavsniff wsplugin # install Wireshark MAVlink disector plugin for reading Mavlink packets
```

Available device urls:
 * `-d /dev/ttyS0` - standard serial port on UNIX systems
 * `-d COMx` - from COM1 to COM8 - standard serial ports on Windows systems
 * `-d udp://<host>:<port>` or `tcp://<host>:<port>` - receive or send packets over network (TCP or UDP)
 * currently, there is no option how to **send** MAVLink packets over the network.

### Using with network

mavsniff uses compatible format of UDP packets with QGroundControl. That means if you capture packets
emitted (mirrored) by QGroundControl with Wireshark then you will be able to replay those to any serial
device. Those packets have minimal ethernet header `02 00 00 00` and uses 20 bytes long IP header and
only 8 bytes for a UDP header. Any other packets will not be replayable by mavsniff.


## Developement

Start developing by cloning the repo and installing tha application locally

```bash
$ git clone git@github.com:katomaso/mavsniff.git && cd mavsniff
$ python -m venv .venv
$ pip install -e .[dev]  # to install even the extra dev dependencies
```

After developing new features, run tests and build and publish new package

```bash
$ pytest
$ python3 -m build
$ python -m twine upload dist/*
```
