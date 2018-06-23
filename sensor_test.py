import time

import RPi.GPIO as GPIO

from raspi_master import get_distance_from_sensor_in_cm, setup_gpio

def sensor_reading():
    while True:
        print("Distance: {} cm".format(get_distance_from_sensor_in_cm()))

        time.sleep(1.5)

if __name__ == '__main__':
    try:
        setup_gpio()
        sensor_reading()
        GPIO.cleanup()
    except:
        GPIO.cleanup()