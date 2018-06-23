import math
import os 
import time

import RPi.GPIO as GPIO

from raspi_master import calibrate, get_distance_from_sensor_in_cm, setup_gpio

SETTINGS_DIR = '/home/pi/settings'

def main(cal=True):
    settings_file = SETTINGS_DIR + '/threshold.txt'
    if not os.path.isfile(settings_file) and not cal:
        # Set defauly threshold value if no settigns file exists
        CLOSED_DOOR_DISTANCE_CM = 50 # About 5.5ft
    elif not os.path.isfile(settings_file) and cal:
        # If cal is set to True
        CLOSED_DOOR_DISTANCE_CM = calibrate()

        if CLOSED_DOOR_DISTANCE_CM != -1:
            with open(settings_file, 'w') as threshold_file:
                # Write the new threshold value to the settings folder
                threshold_file.write('CLOSED_DOOR_DISTANCE_CM = {}'.format(CLOSED_DOOR_DISTANCE_CM))

    else:
        # If cal is set to false
        with open(settings_file, 'r') as threshold_file:
            # Read variable value from text file
            file_data = threshold_file.readlines()

        for line in file_data:
            split_line = line.split('=')
            key = split_line[0]
            value = split_line[1]
            if key == 'CLOSED_DOOR_DISTANCE_CM':
                CLOSED_DOOR_DISTANCE_CM = value

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
        #main(cal=False)
        #sensor_reading()
        print(calibrate())
        GPIO.cleanup()
    except:
        GPIO.cleanup()
