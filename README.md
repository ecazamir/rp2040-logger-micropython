# Pre-requisites for the software to work

## Install Micropython on your device

Go to [Micropython downloads page](https://micropython.org/download/), grab the package and install it on yout device

## Install libraries

| Library | Command | Required for |
|---|---|---|
| SD Card library | `mpremote mip install sdcard` | Mount SD card under /sd |
| SparkFun Qwiic I2C | `mpremote mip install github:sparkfun/qwiic_i2c_py` | SparkFun flavor of I2C library |
| SparkFun Qwiic RTC RV 8803 | `mpremote mip install github:sparkfun/qwiic_rv-8803_py` | Adds support for hardware RTC |
| SparkFun Qwiic ADC 4 Channel ADS1015 | `# mpremote mip install github:sparkfun/qwiic_ads1015_py` | Adds support for ADC based on ADS1015 |

Certain libraries won't be installable with mpremote. For these, go grab them directly and copy them to the `/lib` directory on your device (Thonny IDE can help you do that very well)

| Library | Required for |
|---|---|
| [Robert Hammelrath's ADS1x15 library](https://github.com/robert-hh/ads1x15/blob/master/ads1x15.py) | Adds support for ADC based on ADS1015 |

# Install the code

- Copy `boot.py` to your device
- Copy `main.py` to your device

## Adapt it to your setup

This piece of software was written for SparkFun Thing Plus RP2040. If you have a different device, please adapt the numbers of pins in `boot.py`. known working micropython versions: 1.24.1, 1.25.0. 

# Run it!
