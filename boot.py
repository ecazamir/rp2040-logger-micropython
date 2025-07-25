from ads1x15 import ADS1115,ADS1015
import qwiic_max1704x
import qwiic_rv8803
from sdcard import SDCard
from machine import RTC,I2C
import os,utime

# One might find strange that two I2C objects are used. One is for Qwiic-like devices,
# accesed through qwiic_i2c library
# The other is for devices connected to a lower-level machine.I2C bus. 

# Log storage location
SD_MOUNT_PATH = "/sd"

# I2C Parameters
I2C_SDA_Pin = 6
I2C_SCL_Pin = 7
I2C_Frequency = 100000

# Other board-specific values
SPI_CS_Pin = 9
LED_Pin = 25
RGB_LED_Pin = 8

# Known device addresses
# BG_MAX1704x = Battery gauge  found in most Sparkfun boards
# ADC_ADS1x15 = ADS1x15-based multi-channel ADC. This software uses the library found here to drive this https://github.com/robert-hh/ads1x15
# RTC_RV8803 = High precision Real time clock module with temperature compensation
I2C_Addr_BG_MAX1704x = 0x36
I2C_Addr_ADC_ADS1x15 = 0x48
I2C_Addr_RTC_RV8803 = 0x32
I2C_Attached_BG_MAX1704x = False
I2C_Attached_ADC_ADS1x15 = False
I2C_Attached_RTC_RV8803 = False

# ADC related parameters
# ADC_Multiplier represents the division factor used on input channel 0 of the ADC
ADC_MULTIPLIER_A0 = 10.0
# Valid values for ADC Chip: ADS1015 and ADS1115
ADC_CHIP = 'ADS1115'

# Clock resync interval
# When a RTC clock is attached, resync RTC from the real time clock every number of seconds
Clock_Adjust_ms_per_second = 0

# I2C Device Map
i2c_device_aliases = {
    I2C_Addr_RTC_RV8803: "RV-8803 Real time clock",
    I2C_Addr_BG_MAX1704x: "MAX1704x Battery Gauge",
    I2C_Addr_ADC_ADS1x15: "ADS1x15 ADC",
}

# Initialize Machine RTC resource
rtc = machine.RTC()

# Initialize machine.I2C object
try:
    print("Initialize I2c Bus object - uPy native I2C")
    machine_i2c = I2C(freq=I2C_Frequency)
except Exception as e:
    print("Machine I2C error", e)

# Initialize a qwiic I2C bus object
try:
    import qwiic_i2c
    print("Initialize I2c Bus object - qwiic I2C")
    qwiic_i2c = qwiic_i2c.get_i2c_driver(sda=I2C_SDA_Pin, scl=I2C_SCL_Pin, freq=I2C_Frequency)
except Exception as e:
    print("Qwiic I2C error", e)

# Scan qwiic_i2c bus
qwiic_i2c_device_addresses = qwiic_i2c.scan()
print("Qwiic.I2C Bus scan result:")
try:
    for i2c_device_address in qwiic_i2c_device_addresses:
        print(
            f"  found device at 0x{i2c_device_address:02x}, assuming {i2c_device_aliases[i2c_device_address]}"
        )
except Exception as e:
    print("  Qwiic I2C Scan: Unknown device", e)

# Set booleans for clock etc
if I2C_Addr_RTC_RV8803 in qwiic_i2c_device_addresses:
    I2C_Attached_RTC_RV8803 = True

# Subroutine to sync RTC from Hardware RTC
# Synchronize the cpu RTC from external module
def sync_rtc_from_hw_clock():
    if I2C_Attached_RTC_RV8803:
        HW_RTC_RV_8803.update_time()
        rtc.datetime(
            (
                HW_RTC_RV_8803.get_year(),
                HW_RTC_RV_8803.get_month(),
                HW_RTC_RV_8803.get_date(),
                HW_RTC_RV_8803.get_weekday(),
                HW_RTC_RV_8803.get_hours(),
                HW_RTC_RV_8803.get_minutes(),
                HW_RTC_RV_8803.get_seconds(),
                HW_RTC_RV_8803.get_hundredths(),
            )
        )

# Look for SparkFun RV-8803 module and display message
if I2C_Attached_RTC_RV8803:
    print(
        f"I2C: Treating device at 0x{I2C_Addr_RTC_RV8803:02x} as SparkFun RTC module RV-8803"
    )
    HW_RTC_RV_8803 = qwiic_rv8803.QwiicRV8803(
        address=I2C_Addr_RTC_RV8803, i2c_driver=qwiic_i2c
    )
    HW_RTC_RV_8803.begin()
    HW_RTC_RV_8803.set_24_hour()
    HW_RTC_RV_8803.update_time()
    print("RTC Date and time: " + HW_RTC_RV_8803.string_time_8601())
    # Setting machine RTC using values from the hardware RTC module
    # https://docs.micropython.org/en/latest/library/machine.RTC.html
    # Parameter order: (year, month, day, weekday, hours, minutes, seconds, subseconds)
    sync_rtc_from_hw_clock()

else:
    print("I2C: Real Time Clock module not found, using local RTC instead")
    mdt = machine.RTC().datetime()
    print(
        f"Machine RTC: {mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}T{mdt[4]:02d}:{mdt[5]:02d}:{mdt[6]:02d}"
    )

# Set boolean for the presence of the I2C ADC based on ADS1x15
if I2C_Addr_ADC_ADS1x15 in qwiic_i2c_device_addresses:
    I2C_Attached_ADC_ADS1x15 = True

    print(
        f"I2C: Treating device at 0x{I2C_Addr_ADC_ADS1x15:02x} as {ADC_CHIP} using the ads1x15 library"
    )
    if ADC_CHIP == 'ADS1115':
        ADC_MODULE = ADS1115(machine_i2c, address=I2C_Addr_ADC_ADS1x15, gain=1)
    elif ADC_CHIP == 'ADS1015':
        ADC_MODULE = ADS1015(machine_i2c, address=I2C_Addr_ADC_ADS1x15, gain=1)
else:
    print("I2C: ADC ADS 1x15 module not found, not using it")

# Initialize the battery gauge
if I2C_Addr_BG_MAX1704x in qwiic_i2c_device_addresses:
    MAX1704x_BATTERY_GAUGE=qwiic_max1704x.QwiicMAX1704X(device_type=qwiic_max1704x.QwiicMAX1704X.kDeviceTypeMAX17048, address=I2C_Addr_BG_MAX1704x, i2c_driver=qwiic_i2c)
    if MAX1704x_BATTERY_GAUGE.is_connected():
        MAX1704x_BATTERY_GAUGE.begin()
        # Only set the attached flag if the connection and begin() are successful
        I2C_Attached_BG_MAX1704x = True
        print("I2C connection to MAX1704x battery gauge successful.")
        print(f"  MAX1704x: Device ID: 0x{MAX1704x_BATTERY_GAUGE.get_id():02X}")
        print(f"  MAX1704x: Device version: 0x{MAX1704x_BATTERY_GAUGE.get_version():02X}")
        MAX1704x_BATTERY_GAUGE.reset()
        utime.sleep(1)
        # print("Battery empty threshold is currently: {}%".format(MAX1704x_BATTERY_GAUGE.get_threshold()))
        # MAX1704x_BATTERY_GAUGE.set_threshold(10) # Set alert threshold to 10%.
        # high_voltage = MAX1704x_BATTERY_GAUGE.get_valrt_max() * 0.02 # 1 LSb is 20mV. Convert to Volts.
        # print("High voltage threshold is currently: {:.2f}V".format(high_voltage))
        
        print(f"  MAX1704x: Voltage: {MAX1704x_BATTERY_GAUGE.get_voltage():.3f}V")  # Print the battery voltage
        print(f"  MAX1704x: SOC Percentage: {MAX1704x_BATTERY_GAUGE.get_soc():.2f}%")  # Print the battery state of charge with 2 decimal places
        print(f"  MAX1704x: Change Rate: {MAX1704x_BATTERY_GAUGE.get_change_rate():.3f}%/hr")  # Print the battery change rate with 3 decimal places
        print(f"  MAX1704x: Alert flag: {MAX1704x_BATTERY_GAUGE.get_alert()}")  # Print the generic alert flag
        print(f"  MAX1704x: Voltage High Alert: {MAX1704x_BATTERY_GAUGE.is_voltage_high(True)}")  # Print the alert flag. Passing "True" also clears the flag
        print(f"  MAX1704x: Voltage Low Alert: {MAX1704x_BATTERY_GAUGE.is_voltage_low(True)}")  # Print the alert flag. Passing "True" also clears the flag
        print(f"  MAX1704x: Empty Alert: {MAX1704x_BATTERY_GAUGE.is_low()}")  # Print the alert flag
        print(f"  MAX1704x: SOC 1% Change Alert: {MAX1704x_BATTERY_GAUGE.is_change()}")  # Print the alert flag
        print(f"  MAX1704x: Hibernating: {MAX1704x_BATTERY_GAUGE.is_hibernating()}")  # Print the hibernation flag
        
    else:
        print("I2C connection to MAX1704x battery gauge failed.")



# Mount the SD card
try:
    print("Trying to mount the SD card...")
    spi1 = machine.SPI(1)
    # on SparkFun Thing Plus 2040 The embedded SD card is at SPI(1)
    # gpio 12(miso), 14(sck) and 15(mosi), with CS on pin 9
    sd = SDCard(spi1, machine.Pin(SPI_CS_Pin))
    vfs = os.VfsFat(sd)
    os.mount(vfs, SD_MOUNT_PATH)
    print("SD card mounted under " + SD_MOUNT_PATH)

except Exception as e:
    print("An error occurred while mounting the SD card:", e)
