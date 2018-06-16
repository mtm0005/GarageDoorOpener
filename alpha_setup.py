import os
import time

from raspi_master import calibrate

SETTINGS_DIR = '/Users/tylersherrod/Desktop/settings'

def main(cal=True):
    settings_file = SETTINGS_DIR + '/threshold.txt'
    if not os.path.isfile(settings_file) and not cal:
        # Set defauly threshold value if no settigns file exists
        MAX_CLOSED_DOOR_DISTANCE_CM = 170 # About 5.5ft
    elif not os.path.isfile(settings_file) and cal:
        # If cal is set to True
        MAX_CLOSED_DOOR_DISTANCE_CM = calibrate()

        if MAX_CLOSED_DOOR_DISTANCE_CM != -1:
            with open(settings_file, 'w') as threshold_file:
                # Write the new threshold value to the settings folder
                threshold_file.write('MAX_CLOSED_DOOR_DISTANCE_CM = {}'.format(MAX_CLOSED_DOOR_DISTANCE_CM))

    else:
        # If cal is set to false
        with open(settings_file, 'r') as threshold_file:
            # Read variable value from text file
            file_data = threshold_file.read()
            MAX_CLOSED_DOOR_DISTANCE_CM = file_data.split()[-1]

    

if __name__ == '__main__':
    main(cal=False)