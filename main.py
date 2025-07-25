# Assumes certain variables are defined by boot.py:
# I2C_Attached_RTC_RV8803 set to true if a hardware clock module is attached
#  if that is the case, then a clock object HW_RTC_RV_8803 should be defined.
# Otherwise, machine.RTC().datetime() is used.

print("\nStarting main: ")

from machine import RTC, Timer, Pin
import neopixel  # Control onboard RGB LED

# from time import sleep
import utime

led_pin = Pin(LED_Pin, Pin.OUT)
np = neopixel.NeoPixel(machine.Pin(RGB_LED_Pin), 1)

def get_timestamp():
    # This is used to populate log entries
    # Returns date and time as string, relative to UTC
    if I2C_Attached_RTC_RV8803:
        HW_RTC_RV_8803.update_time()
        timestamp_string = f"{HW_RTC_RV_8803.string_time_8601()}"
    else:
        mdt = machine.RTC().datetime()
        timestamp_string = f"{mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}T{mdt[4]:02d}:{mdt[5]:02d}:{mdt[6]:02d}"
    return timestamp_string


# Blinks the led 1, 2 or 3 times, depending on the range of a value received as parameter
# and two threshold values.
def blink(low_watermark=1500.0, high_watermark=1600.0, current_value=0.0):
    if current_value < low_watermark:
        blink_count = 1
    else:
        if current_value > high_watermark:
            blink_count = 3
        else:
            blink_count = 2
    for counter in range(blink_count):
        led_pin.on()
        utime.sleep(0.02)
        led_pin.off()
        utime.sleep(0.10)


def rgb_led_for_12v_efb(current_value=0.0):
    critical_threshold = 11.580  # 21%
    low_threshold = 12.00   # 45%
    good_threshold = 12.20  # 60%
    very_good_threshold = 12.42  # 80%
    full_threshold = 12.60  # 100%
    color = (20, 20, 20)
    if current_value < critical_threshold:
        color = (10, 0, 0)  # Red
    elif current_value < low_threshold:
        color = (12, 8, 0)  # Orange-Red
    elif current_value < good_threshold:
        color = (4, 10, 0)  # Green-Yellow
    elif current_value < very_good_threshold:
        color = (0, 10, 4)  # Green-Blue
    elif current_value < full_threshold:
        color = (0, 4, 12)  # Blue
    else:  # Above full voltage
        color = (10, 0, 10)  # Mov
    np[0] = color
    np.write()


def get_log_file_name():
    if I2C_Attached_RTC_RV8803:
        # a new readout of the clock is not done, it is assumed that this is called immediately afetr get_timestamp()
        date_ymd = f"{HW_RTC_RV_8803.get_year():04d}{HW_RTC_RV_8803.get_month():02d}{HW_RTC_RV_8803.get_date():02d}"
    else:
        date_ymd = f"{mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}".format(
            mdt=machine.RTC().datetime()
        )

    log_file_name = f"{SD_MOUNT_PATH}/log-{date_ymd}.log"
    return log_file_name


# log_data will read the sensors and write to the log file.
# it will be invoked on timer interrupt

def main_loop_cb(timer=None):
    try:
        # Get the timestamp
        timestamp = get_timestamp()
        log_file_name = get_log_file_name()

        # Read voltage from ADC_ADS1115, 16 bit, using the ads1x15 library
        if I2C_Attached_ADC_ADS1x15:
            adc_voltage_divisor_factor_a0 = ADC_MULTIPLIER_A0
            adc_voltage_channel_a0 = ADC_MODULE.raw_to_v(ADC_MODULE.read(rate=0, channel1=0))
            effective_voltage_a0 = ADC_MULTIPLIER_A0 * adc_voltage_channel_a0
            adc0_value = f"{effective_voltage_a0:.3f}"
        else:
            adc0_value = "NaN"

        # adc2_value = 12.2
        battery_gauge_info = '"BG_VOLTAGE","BG_SOC"'
        if I2C_Attached_BG_MAX1704x:
            battery_gauge_info = f'"{MAX1704x_BATTERY_GAUGE.get_voltage():.3f}","{MAX1704x_BATTERY_GAUGE.get_soc():.2f}"'
        # Format log entry
        log_entry = f'"{timestamp}",{battery_gauge_info},"{adc0_value}"'

        # Write to the file
        with open(log_file_name, "a") as log_file:
            log_file.write(log_entry + "\n")
            print(f"Logged successfully: {log_file_name}: {log_entry}")
            log_file.close()
        # EFB battery SOC: 11.90 = 40%, 12.32 = 70%
        # https://www.briskoda.net/forums/topic/489933-anyone-know-what-battery-voltage-efb-there-should-be/
        blink()
        if I2C_Attached_ADC_ADS1x15:
            rgb_led_for_12v_efb(current_value=effective_voltage_a0)
    except Exception as e:
        print("log_data: An error occurred acquiring data or saving it to the log:", e)


print(f"Timestamp: {get_timestamp()}")
led_pin.off()
# Keep the program running
if I2C_Attached_ADC_ADS1x15:
    try:
        timer_ms_interval = 1000 + Clock_Adjust_ms_per_second
        print("Creating the timer with callback to log_data()")
        log_timer = Timer(period=timer_ms_interval, mode=Timer.PERIODIC, callback=main_loop_cb)
        print("Entering the loop...")
        while True:
            utime.sleep(1)
    except KeyboardInterrupt:
        # Clean up and stop the timer on keyboard interrupt
        log_timer.deinit()
        print("Keyboard Interrupt, terminating program")
else:
    led_pin.on()
    print("An ADC module is not found. Terminating program.")
