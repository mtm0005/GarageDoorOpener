import math
import os 
import time

import RPi.GPIO as GPIO

from raspi_master import calibrate, get_distance_from_sensor_in_cm, setup_gpio

SETTINGS_DIR = '/home/pi/settings'

def main(cal=True):
    settings_file = SETTINGS_DIR + '/threshold.txt'
    if not os.path.isfile(settings_file) and not cal:
        # Set default threshold value if no settigns file exists
        print('Set default threshold')
        CLOSED_DOOR_DISTANCE_CM = 50 # About 5.5ft
    elif cal:
        # If cal is set to True
        print('Entering calibrate function')
        CLOSED_DOOR_DISTANCE_CM = calibrate()
    else:
        # If cal is set to false
        print('Reading threshold settings file')
        with open(settings_file, 'r') as threshold_file:
            # Read variable value from text file
            file_data = threshold_file.readlines()

        for line in file_data:
            split_line = line.split('=')
            key = split_line[0]
            value = split_line[1]
            if key == 'CLOSED_DOOR_DISTANCE_CM':
                CLOSED_DOOR_DISTANCE_CM = value

    return CLOSED_DOOR_DISTANCE_CM

def sensor_reading():
    prev_reading = int(get_distance_from_sensor_in_cm())
    while True:
        new_reading = int(get_distance_from_sensor_in_cm())
        print("{} ------> {}".format(prev_reading, new_reading))
        percent_diff = int(100*math.fabs(new_reading-prev_reading)/prev_reading)
        print('Percentage difference: {}'.format(percent_diff))

        prev_reading = new_reading
        time.sleep(1.5)

if __name__ == '__main__':
    try:
        setup_gpio()
        print(main(cal=True))
        #sensor_reading()
        GPIO.cleanup()
    except:
        GPIO.cleanup()
