import datetime
import pyfcm
import RPi.GPIO as GPIO
import time

from enum import Enum
from firebase import firebase

TRIG_PIN = 7
ECHO_PIN = 12
GARAGE_DOOR_PIN = 11

FIREBASE_URL = 'https://garagedoortest-731f7.firebaseio.com/'
API_KEY = 'AIzaSyC9qjcqNPZsUOUU0fBTTV5b5I1GT89oxb4'

MAX_CLOSED_DOOR_DISTANCE_CM = 91 # Just under 3 feet

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
    command = firebase_connection.get('command', None)

    if command:
        # Clear the command field on firebase so that the App knows it has
        # been received.
        firebase_connection.put('', 'command', '')
        print_with_timestamp('Received command: {}'.format(command))

    return command

def get_distance_from_sensor_in_cm():
    distance_sum = 0
    num_samples = 10
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

def notify_user(firebase_connection, status: DoorState):
    print_with_timestamp('Sending notification to user')
    push_service = pyfcm.FCMNotification(api_key=API_KEY)
    device_id = 'device {}'.format(firebase_connection.get('device ID', None))
    result = push_service.notify_single_device(registration_id=device_id,
        message_title='Garage door update', message_body=status.name)

    if not result['success']:
        print_with_timestamp('notification failed to send')
        with open('notification_failures.txt', 'a') as errors_file:
            errors_file.write('Notification failure occurred at {}\n'.format(datetime.datetime.now()))
            errors_file.write('Attempted to send msg_title: Garage door update\n')
            errors_file.write('               and msg_body: {}\n'.format(status.name))
            errors_file.write('to device: {}\n'.format(device_id))
            errors_file.write('with api_key: {}\n'.format(API_KEY))
            errors_file.write('\n-------------------------------------------------\n')

    return result

def main():
    setup_gpio()
    firebase_connection = get_firebase_connection()
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

        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
        print_with_timestamp('returned from main')
        GPIO.cleanup()
    except Exception as e:
        print_with_timestamp('exception occurred')
        print(e)
        GPIO.cleanup()
