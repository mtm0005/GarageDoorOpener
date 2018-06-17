import datetime
import math
import os
import pyfcm
import RPi.GPIO as GPIO
import subprocess
import time
import traceback

from enum import Enum
from firebase import firebase

TRIG_PIN = 7
ECHO_PIN = 12
GARAGE_DOOR_PIN = 11

FIREBASE_URL = 'https://garagedoortest-731f7.firebaseio.com/'
API_KEY = 'AIzaSyC9qjcqNPZsUOUU0fBTTV5b5I1GT89oxb4'
BASE_LOG_DIR = '/home/pi/log_files'
SETTINGS_DIR = '/home/pi/settings'

MAX_CLOSED_DOOR_DISTANCE_CM = 170 # About 5.5ft
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

def get_serial():
    # Extract serial from cpuinfo file
    cpuserial = '0000000000000000'
    try:
        with open('/proc/cpuinfo','r') as f:
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
    except:
        cpuserial = 'ERROR000000000'

    return cpuserial

def calibrate():
    reading_diff_limit = 0.05 # Subsequent readings must be within 5% of each other
    initial_diff_limit = 0.5 # New reading must be at least 50% different from initial reading

    # Take current reading
    first_reading = get_distance_from_sensor_in_cm()
    time.sleep(.5)

    # Toggle garage door state
    toggle_door_state()

    # Check reading until value changes
    reading_diff = 100
    initial_diff = 0
    prev_reading = first_reading
    while reading_diff > reading_diff_limit and initial_diff < initial_diff_limit:
        new_reading = get_distance_from_sensor_in_cm()

        reading_diff = (new_reading - prev_reading)/prev_reading
        initial_diff = (new_reading - first_reading)/first_reading
        time.sleep(1)

    # Set threshold as average of two readings
    temporary_threshold = math.fabs((new_reading - first_reading)/2)

    # TO-DO: verify this comparator is correct for the raspberry pi location
    if new_reading >= temporary_threshold:
        prev_state = DoorState.open
    else:
        prev_state = DoorState.closed

    toggle_door_state()

    new_state = prev_state
    start_time = time.time()
    while new_state != prev_state:
        time_diff = time.time() - start_time

        reading = get_distance_from_sensor_in_cm()
        # TO-DO: verify this comparator is correct for the raspberry pi location
        if reading >= temporary_threshold:
            new_state = DoorState.open
        else:
            new_state = DoorState.closed

        # If exceed timeout, calibrate failed
        if time_diff > 30:
            return -1
        time.sleep(2)

    return temporary_threshold

def get_door_state_from_str(door_state_string: str):
    door_state_string = door_state_string.strip().lower()
    if (door_state_string == 'open'):
        return DoorState.open
    elif (door_state_string == 'closed'):
        return DoorState.closed
    else:
        return DoorState.unknown

def git_pull():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    raw_output = subprocess.check_output('git pull'.split())
    return raw_output.decode('ascii')

def print_with_timestamp(msg):
    print('{} - {}'.format(datetime.datetime.now(), msg))

def setup_gpio():
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.output(TRIG_PIN, 0)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    GPIO.setup(GARAGE_DOOR_PIN, GPIO.OUT)
    GPIO.output(GARAGE_DOOR_PIN, 0)

def get_firebase_connection():
    return firebase.FirebaseApplication(FIREBASE_URL)

def get_command(firebase_connection):
    command = firebase_connection.get('door-{}.command'.format(RASPI_SERIAL_NUM), None)

    if command:
        # Clear the command field on firebase so that the App knows it has
        # been received.
        firebase_connection.put('door-{}'.format(RASPI_SERIAL_NUM), 'command', '')
        print_with_timestamp('Received command: {}'.format(command))

    return command

def get_status(firebase_connection):
    return firebase_connection.get('door-{}.status'.format(RASPI_SERIAL_NUM), None)

def get_distance_from_sensor_in_cm():
    distance_sum = 0
    num_samples = 20
    for i in range(num_samples):
        GPIO.output(TRIG_PIN, 1)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, 0)

        while GPIO.input(ECHO_PIN) == 0:
            pass

        start = time.time()

        while GPIO.input(ECHO_PIN) == 1:
            pass

        stop = time.time()
        distance_sum += stop - start
        time.sleep(0.01)

    distance_avg = distance_sum/num_samples 

    return distance_avg * 17000

def toggle_door_state():
    print_with_timestamp('Toggling door state')
    GPIO.output(GARAGE_DOOR_PIN, 1)
    time.sleep(0.4)
    GPIO.output(GARAGE_DOOR_PIN, 0)

def set_threshold():
    settings_file = SETTINGS_DIR + '/threshold.txt'
    if os.path.isfile(settings_file):
        with open(settings_file, 'r') as threshold_file:
            # Read variable value from text file
            file_data = threshold_file.read()
            return file_data.split()[-1]
    else:
        return MAX_CLOSED_DOOR_DISTANCE_CM

def check_door_status():
    distance_in_cm = get_distance_from_sensor_in_cm()

    if distance_in_cm > MAX_CLOSED_DOOR_DISTANCE_CM:
        return DoorState.open
    else:
        return DoorState.closed

def open_door():
    if check_door_status() == DoorState.closed:
        toggle_door_state()

def close_door():
    if check_door_status() == DoorState.open:
        toggle_door_state()

def update_status(firebase_connection, status):
    firebase_connection.put('', 'status', status.name)

def process_command(firebase_connection, command):
    print_with_timestamp('Processing command: {}'.format(command))
    if command == ValidCommands.checkDoorStatus.name:
        print_with_timestamp('checkDoorStatus command')
        status = check_door_status()
        update_status(firebase_connection, status)
        print('Door is {}'.format(status.name))
    elif command == ValidCommands.openDoor.name:
        print_with_timestamp('openDoor command')
        open_door()
    elif command == ValidCommands.closeDoor.name:
        print_with_timestamp('closeDoor command')
        close_door()
    else:
        print_with_timestamp('invalid command')
        log_info('processed-invalid-command', data=command)

def notify_user(firebase_connection, status: DoorState):
    print_with_timestamp('Sending notification to user')
    push_service = pyfcm.FCMNotification(api_key=API_KEY)
    device_id = 'device {}'.format(
        firebase_connection.get('door-{}.device ID'.format(RASPI_SERIAL_NUM), None))
    result = push_service.notify_single_device(registration_id=device_id,
        message_title='Garage door update', message_body=status.name)

    if not result['success']:
        print_with_timestamp('notification failed to send')
        log_info('notification-failure', data=status.name)

    return result

# TO-DO: Add software version to each message.
def log_info(group: str, data=None):
    # Make sure the BASE_LOG_DIR exists
    if not os.path.isdir(BASE_LOG_DIR):
        os.mkdir(BASE_LOG_DIR)

    current_time = datetime.datetime.now().strftime('%H_%M_%S')
    current_date = datetime.date.today().strftime('%Y_%m_%d')
    file_path = '{}/{}.txt'.format(BASE_LOG_DIR, current_date)
    with open(file_path, 'a') as log_file:
        # Write the message and the exception to that file.
        log_file.write('{} | {} | {}\n'.format(current_time, group, data))

def main():
    log_info('bootup')

    # TO-DO: Check if threshold file is created or set default threshold
    global MAX_CLOSED_DOOR_DISTANCE_CM
    MAX_CLOSED_DOOR_DISTANCE_CM = set_threshold()

    global RASPI_SERIAL_NUM
    RASPI_SERIAL_NUM = get_serial()

    setup_gpio()
    firebase_connection = get_firebase_connection()
    
    previous_door_state = get_door_state_from_str(get_status(firebase_connection))
    if not previous_door_state:
        previous_door_state = DoorState.unknown

    while True:
        command = get_command(firebase_connection)
        if command:
            process_command(firebase_connection, command)

        current_door_state = check_door_status()
        if current_door_state != previous_door_state:
            previous_door_state = current_door_state
            update_status(firebase_connection, current_door_state)
            notify_user(firebase_connection, current_door_state)

        # Exit if there is an update.
        if git_pull() != 'Already up-to-date.\n':
            log_info('update')
            return 0

        time.sleep(0.5)

if __name__ == '__main__':
    try:
        main()
        print_with_timestamp('returned from main')
        GPIO.cleanup()
    except BaseException as e:
        GPIO.cleanup()
        print_with_timestamp('exception occurred')
        log_info('exception', data=e)
