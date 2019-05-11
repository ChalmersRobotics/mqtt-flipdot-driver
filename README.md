# MQTT FlipDot Display Driver

This repository contains a python driver for interfacing the Mobitec FlipDot Displays that we have at CRF via simple MQTT messages. The idea is to use the displays for displaying various data and messages, for example the status of our 3D-printers.

## Hardware

The displays communicate over a serial link at 4800 baud using RS-485. Each one have a different address (as indicated in the driver) selectable by on-board dip switches.

Powered using +20-24 volts.

## Installation

First clone this repository and enter the newly created directory

```bash
git clone XXXXX
cd mqtt-flipdot-driver
```

### Using `pipenv`

The project uses `pipenv` to manage all dependencies. Make sure you have `pipenv` installed before proceding. If not, you can install it using

```bash
pip install pipenv
```

> You may need to run the command as sudo and/or using `python -m pip install pipenv`

 and run the following comand:

```bash
pipenv install
```

This will install all required dependencies.

### Without 'pipenv'

If `pipenv` somehow didn't work (happens of Raspberry Pi because Python 3.7.0 is not yet available for it as of this writing) or is not available, use the following command to install the required dependencies.

```bash
pip install PyYAML paho-mqtt pyserial
```

## Similar projects

Here are some links that we found useful while developing this project. They contain more information about the hardware used and some reverse enginered protocol detatils.

* [Building an Android-controlled Flip-Disc Display](http://www.scottcutler.net/projects/flipdots/flipdots.html)
* [Adventures with Flippy the Flip-dot Display](https://engineer.john-whittington.co.uk/2017/11/adventures-flippy-flip-dot-display/)
* [Svenska ElektronikForumet: Mobitec flipdot RS-485 protokoll](https://elektronikforumet.com/forum/viewtopic.php?f=2&t=65264)
* [Brose Vollmatrix](https://code.trafficking.agency/brose-vollmatrix.html)

* [GitHub: mobitec rs485 flip-dot display example](https://github.com/duffrohde/mobitec-rs485)
* [GitHub: Controller software for the flipdot displays](https://github.com/openspaceaarhus/flipdot)

* [Matrix hardware reverse engineered setup](https://github.com/openspaceaarhus/flipdot/blob/master/flipper/master_setup.pdf)

## Datasheets

* [FP2800A Decoder Driver](http://pdf.datasheetcatalog.com/datasheets/320/500899_DS.pdf)
* [MC33063A Buck Converter](https://www.ti.com/lit/ds/symlink/mc33063a.pdf)
* [PD71055 Parallel Interface](https://pdf1.alldatasheet.com/datasheet-pdf/view/7017/NEC/D71055C.html)
* [SN75176A Differential Bus Transceiver](https://www.ti.com/lit/ds/symlink/sn75176a.pdf)
* [TSC80C31-12IA: Single-chip 8 Bit Microcontroller](https://www.digchip.com/datasheets/parts/datasheet/779/TSC80C31-12IA.php)