import datetime
import math
import os
import RPi.GPIO as GPIO
import time 

from enum import Enum

import firebase_utils
import git_utils
import utils

TRIG_PIN = 7
ECHO_PIN = 12
GARAGE_DOOR_PIN = 11

FIREBASE_URL = 'https://garagedoortest-731f7.firebaseio.com/'
API_KEY = 'AIzaSyC9qjcqNPZsUOUU0fBTTV5b5I1GT89oxb4'
SETTINGS_DIR = '/home/pi/settings'
DRIVE_AUTH = None

OPEN_DOOR_DISTANCE_CM = 25
PERCENTAGE_THRESHOLD = 0.5
RASPI_SERIAL_NUM = None

class DoorState(Enum):
    open = 1
    closed = 2
    unknown = 3

# TODO: Add a function for each enumeration so that the
# process_command function can loop over all commands generically and
# call the appropriate function for the specified command.
class ValidCommands(Enum):
    checkDoorStatus = 1
    openDoor = 2
    closeDoor = 3
    updateLogFile = 4
    calibrate = 5

def calibrate(firebase_connection):
    firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'status', 'calibrating')

    # Readings must be 70% different than initial reading
    initial_diff_limit = 0.7

    # Take current reading
    first_reading = get_distance_from_sensor_in_cm()
    print('Initial reading: {} cm'.format(first_reading))

    # Toggle garage door state
    print('Toggle')
    toggle_door_state()

    # Check reading until value changes
    print('Monitoring...')
    initial_diff = 0
    while initial_diff < initial_diff_limit:
        time.sleep(5)
        new_reading = get_distance_from_sensor_in_cm()
        
        initial_diff = math.fabs(new_reading - first_reading)/first_reading
        print('{} cm | {} diff'.format(new_reading, initial_diff))

    # Set second reading
    second_reading = new_reading

    if second_reading > first_reading:
        open_threshold = first_reading
    else:
        open_threshold = second_reading

    print('')
    print('---------------------------------')
    print('open_threshold is set to {} cm'.format(open_threshold))
    print('---------------------------------')
    print('')

    print('Waiting...')
    time.sleep(10)

    first_cal_status = check_door_status(open_threshold)
    print('Door status: {}'.format(first_cal_status.name))

    print('Toggle')
    toggle_door_state()

    start_time = time.time()
    print('Monitoring...')
    while True:
        time.sleep(2)
        current_status = check_door_status(open_threshold)

        if current_status != first_cal_status:
            print('Door status has changed')
            time.sleep(2)
            status_verification = check_door_status(open_threshold)
            if status_verification == current_status:
                print('Door status verified as: {}'.format(current_status))
                break

        if time.time() - start_time > 30:
            print('Calibration timeout')
            return -1

    print('Calibration succeeded')

    if not os.path.isdir(SETTINGS_DIR):
        os.mkdir(SETTINGS_DIR)
    print('Writing threshold to settings file')
    settings_file = SETTINGS_DIR + '/threshold.txt'    
    with open(settings_file, 'w') as threshold_file:
        threshold_file.write('OPEN_DOOR_DISTANCE_CM = {}'.format(open_threshold))

    global OPEN_DOOR_DISTANCE_CM
    OPEN_DOOR_DISTANCE_CM = open_threshold

    time.sleep(5)

    door_state = current_status
    firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'status', door_state.name)
    firebase_utils.notify_users(firebase_connection, RASPI_SERIAL_NUM, API_KEY, door_state)

    return

def get_door_state_from_str(door_state_string: str):
    door_state_string = door_state_string.strip().lower()
    if (door_state_string == 'open'):
        return DoorState.open
    elif (door_state_string == 'closed'):
        return DoorState.closed
    else:
        return DoorState.unknown

def setup_gpio():
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.output(TRIG_PIN, 0)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    GPIO.setup(GARAGE_DOOR_PIN, GPIO.OUT)
    GPIO.output(GARAGE_DOOR_PIN, 0)

def get_sensor_reading():
    GPIO.output(TRIG_PIN, 1)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, 0)

    start = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        if time.time()-start > 1:
            utils.log_info('Sensor timed out')
            utils.print_with_timestamp('Sensor timed out')
            return None

    start = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        pass

    stop = time.time()

    return stop-start

def get_distance_from_sensor_in_cm():
    distance_sum = 0
    num_samples = 20
    max_attempts = 3
    for i in range(num_samples):
        
        reading = get_sensor_reading()
        attempts = 0
        while not reading and attempts < max_attempts:
            reading = get_sensor_reading()
            attempts += 1
        
        if attempts >= max_attempts:
            utils.log_info('sensor-failure', data='attempts: {}'.format(attempts))
            raise Exception('sensor failure - max attempts')

        distance_sum += reading
        time.sleep(0.01)

    distance_avg = distance_sum/num_samples 

    return distance_avg * 17000

def toggle_door_state():
    utils.print_with_timestamp('Toggling door state')
    GPIO.output(GARAGE_DOOR_PIN, 1)
    time.sleep(0.4)
    GPIO.output(GARAGE_DOOR_PIN, 0)

def set_threshold():
    settings_file = SETTINGS_DIR + '/threshold.txt'
    if os.path.isfile(settings_file):
        with open(settings_file, 'r') as threshold_file:
            # Read variable value from text file
            file_data = threshold_file.readlines()

        for line in file_data:
            split_line = line.split('=')
            key = split_line[0].strip()
            value = split_line[1].strip()
            if key == 'OPEN_DOOR_DISTANCE_CM':
                open_threshold = value

        return open_threshold
    else:
        return OPEN_DOOR_DISTANCE_CM

def check_door_status(open_distance=None):
    
    if not open_distance:
        open_distance = OPEN_DOOR_DISTANCE_CM

    open_distance = float(open_distance)

    distance_in_cm = get_distance_from_sensor_in_cm()

    if math.fabs(open_distance-distance_in_cm)/open_distance <= PERCENTAGE_THRESHOLD:
        print('distance: {} is determined to be open'.format(distance_in_cm))
        return DoorState.open
    else:
        print('distance: {} is determined to be closed'.format(distance_in_cm))
        return DoorState.closed

def open_door():
    if check_door_status() == DoorState.closed:
        toggle_door_state()

def close_door():
    if check_door_status() == DoorState.open:
        toggle_door_state()

def update_status(firebase_connection, status):
    firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'status', status.name)

def process_command(firebase_connection, command):
    utils.print_with_timestamp('Processing command: {}'.format(command))
    if command == ValidCommands.checkDoorStatus.name:
        utils.print_with_timestamp('checkDoorStatus command')
        status = check_door_status()
        update_status(firebase_connection, status)
        print('Door is {}'.format(status.name))
    elif command == ValidCommands.openDoor.name:
        utils.print_with_timestamp('openDoor command')
        open_door()
    elif command == ValidCommands.closeDoor.name:
        utils.print_with_timestamp('closeDoor command')
        close_door()
    elif command == ValidCommands.calibrate.name:
        utils.print_with_timestamp('calibrate command')
        calibrate(firebase_connection)
    elif command == ValidCommands.updateLogFile.name:
        utils.print_with_timestamp('updateLogFile command')
        utils.upload_log_file(DRIVE_AUTH, RASPI_SERIAL_NUM, day='today')
    else:
        utils.print_with_timestamp('invalid command')
        utils.log_info('processed-invalid-command', data=command)

def main():
    utils.log_info('bootup', data=git_utils.git_tag())

    # Initial check for update; exit if there is an update
    if git_utils.git_pull() != 'Already up-to-date.\n':
        # TO-DO: This currently logs an update even when there is a git pull error
        utils.log_info('update')
        return 0

    global DRIVE_AUTH
    DRIVE_AUTH = utils.google_auth()

    global OPEN_DOOR_DISTANCE_CM
    OPEN_DOOR_DISTANCE_CM = set_threshold()
    print('Threshold set to {} cm'.format(OPEN_DOOR_DISTANCE_CM))

    global RASPI_SERIAL_NUM
    RASPI_SERIAL_NUM = utils.get_serial()

    setup_gpio()
    firebase_connection = firebase_utils.get_firebase_connection(FIREBASE_URL)
    
    previous_door_state = get_door_state_from_str(firebase_utils.get_status(firebase_connection, RASPI_SERIAL_NUM))
    if not previous_door_state:
        previous_door_state = DoorState.unknown

    while True:
        # Upload log file at 01:00-01:01
        if datetime.datetime.now().hour == 1 and datetime.datetime.now().minute < 2:
            utils.upload_log_file(DRIVE_AUTH, RASPI_SERIAL_NUM)

        command = firebase_utils.get_command(firebase_connection, RASPI_SERIAL_NUM)
        if command:
            process_command(firebase_connection, command)

        current_door_state = check_door_status()
        if current_door_state != previous_door_state:
            # Double check this new reading in case it was faulty
            time.sleep(1)
            door_state_verification = check_door_status()
            if current_door_state == door_state_verification:
                previous_door_state = current_door_state
                update_status(firebase_connection, current_door_state)
                firebase_utils.notify_users(firebase_connection, RASPI_SERIAL_NUM, API_KEY, current_door_state)

        # Exit if there is an update.
        if git_utils.git_pull() != 'Already up-to-date.\n':
            utils.log_info('update')
            return 0

        time.sleep(0.5)

if __name__ == '__main__':
    try:
        main()
        utils.print_with_timestamp('returned from main')
        GPIO.cleanup()
    except BaseException as e:
        GPIO.cleanup()
        utils.print_with_timestamp('exception occurred')
        utils.log_info('exception', data=e)
