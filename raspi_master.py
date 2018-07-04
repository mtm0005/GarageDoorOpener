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
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

TRIG_PIN = 7
ECHO_PIN = 12
GARAGE_DOOR_PIN = 11

FIREBASE_URL = 'https://garagedoortest-731f7.firebaseio.com/'
API_KEY = 'AIzaSyC9qjcqNPZsUOUU0fBTTV5b5I1GT89oxb4'
BASE_LOG_DIR = '/home/pi/log_files'
SETTINGS_DIR = '/home/pi/settings'
DRIVE_AUTH = None

OPEN_DOOR_DISTANCE_CM = 150
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

    cpuserial_strip = cpuserial.lstrip('0')

    return cpuserial_strip

def calibrate(firebase_connection):
    firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'status', 'calibrating')

    # Readings must be 3 times different than initial reading
    initial_diff_limit = 0.7

    # Take current reading
    first_reading = get_distance_from_sensor_in_cm()

    # Toggle garage door state
    print('toggle')
    toggle_door_state()

    # Check reading until value changes
    initial_diff = 0
    while initial_diff < initial_diff_limit:
        time.sleep(5)
        new_reading = get_distance_from_sensor_in_cm()
        print('Sensor reading: {}'.format(new_reading))
        
        initial_diff = math.fabs(new_reading - first_reading)/first_reading
        print('initial_diff: {}'.format(initial_diff))

    # Set second reading
    second_reading = new_reading

    if second_reading > first_reading:
        open_threshold = first_reading
    else:
        open_threshold = second_reading

    print('open threshold: {}'.format(open_threshold))

    #print('waiting for door to stop moving')
    time.sleep(10)

    first_cal_status = check_door_status(open_threshold)
    print('Door status: {}'.format(first_cal_status.name))

    print('toggle')
    toggle_door_state()

    start_time = time.time()
    current_status = first_cal_status
    print('First status: {}'.format(first_cal_status))
    while current_status == first_cal_status:
        time.sleep(2)
        current_status = check_door_status(open_threshold)
        print('current status: {}'.format(current_status))
        if time.time() - start_time > 30:
            print('Calibration timeout')
            return -1

        print('monitoring')

    print('Calibration succeeded')

    if not os.path.isdir(SETTINGS_DIR):
        os.mkdir(SETTINGS_DIR)
    print('making file')
    settings_file = SETTINGS_DIR + '/threshold.txt'    
    with open(settings_file, 'w') as threshold_file:
        threshold_file.write('OPEN_DOOR_DISTANCE_CM = {}'.format(open_threshold))

    global OPEN_DOOR_DISTANCE_CM
    OPEN_DOOR_DISTANCE_CM = open_threshold

    time.sleep(5)

    door_state = check_door_status()
    firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'status', door_state.name)
    notify_users(firebase_connection, door_state)

    return

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

    try:
        raw_output = subprocess.check_output('git pull'.split())
    except BaseException as e:
        log_info('git pull exception', data=e)
        return ''

    return raw_output.decode('ascii')

def git_tag():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    try:
        raw_output = subprocess.check_output('git tag --sort=-refname'.split())
    except BaseException as e:
        return e

    output = raw_output.decode('ascii')

    return output.split()[0]

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
    command = firebase_connection.get('devices/{}/command'.format(RASPI_SERIAL_NUM), None)

    if command:
        # Clear the command field on firebase so that the App knows it has
        # been received.
        firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'command', '')
        print_with_timestamp('Received command: {}'.format(command))
    else:
        # Check for admin command
        # This gives user commands precedence of admin commands
        command = firebase_connection.get('admin/command', None)
        if command:
            # Clear the command field to acknowledge that it has been received
            pass

    return command

def get_status(firebase_connection):
    status = firebase_connection.get('devices/{}/status'.format(RASPI_SERIAL_NUM), None)
    if status == None:
        firebase_connection.put('devices/{}'.format(RASPI_SERIAL_NUM), 'status', '')
        status = ''

    return status

def get_sensor_reading():
    GPIO.output(TRIG_PIN, 1)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, 0)

    start = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        if time.time()-start > 1:
            log_info('Sensor timed out')
            print_with_timestamp('Sensor timed out')
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
            log_info('sensor-failure', data='attempts: {}'.format(attempts))
            raise Exception('sensor failure - max attempts')

        distance_sum += reading
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
    elif command == ValidCommands.calibrate.name:
        print_with_timestamp('calibrate command')
        calibrate(firebase_connection)
    elif command == ValidCommands.updateLogFile.name:
        print_with_timestamp('updateLogFile command')
        upload_log_file(DRIVE_AUTH, day='today')
    else:
        print_with_timestamp('invalid command')
        log_info('processed-invalid-command', data=command)

def notify_users(firebase_connection, status: DoorState):
    print_with_timestamp('Sending notification to user')
    push_service = pyfcm.FCMNotification(api_key=API_KEY)

    # Loop until we get a device ID.
    phone_ids = None
    while not phone_ids:
        phone_ids = firebase_connection.get('devices/{}/phone_IDs'.format(RASPI_SERIAL_NUM), None)
        if not phone_ids:
            time.sleep(1)

    results = []
    for phone in phone_ids.keys():
        result = push_service.notify_single_device(registration_id=phone,
            message_title='Garage door update', message_body=status.name)

        if not result['success']:
            print_with_timestamp('notification failed to send')
            log_info('notification-failure', data=status.name)

        results.append(result)

    return results

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

def google_auth():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)

    return drive

def upload_log_file(drive, day='yesterday'):    
    # Uploads log_file to Google Drive
    print('enter upload log file')
    # Check if settings folder even exists
    if not os.path.isdir(BASE_LOG_DIR):
        print('log folder doesnt exist on Pi')
        return None

    date_file = datetime.datetime.now().strftime('%Y_%m_%d') + '.txt'
    if day == 'yesterday':
        date_file = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(1), '%Y_%m_%d') + '.txt'

    # Determine if error log file exists for the day
    if date_file not in os.listdir(BASE_LOG_DIR):
        print('file does not exist in log folder')
        return None
    
    # Check if Error Logs folder already exists on Google Drive
    print('Checking Google for folder')
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    folderID = None
    for f in file_list:
        if f['title'] == RASPI_SERIAL_NUM + ' - Error Logs':
            folderID = f['id']
    
    # Create Error Logs folder if it doesn't exist
    if not folderID:
        print('Creating Google folder')
        folder = drive.CreateFile({'title': RASPI_SERIAL_NUM + ' - Error Logs', 'mimeType' : 'application/vnd.google-apps.folder'})
        folder.Upload()
        folderID = folder['id']
    else:
        print('Checking Google folder for file')
        # Check if file already exists in folder, return None if file already exists
        driveID = {'q': "'{}' in parents and trashed=false".format(folderID)}
        file_list = drive.ListFile(driveID).GetList()
        for f in file_list:
            if f['title'] == date_file:
                print('file already exists on Google; deleting file')
                f.Delete()

    print('folderID: {}'.format(folderID))
            
    print('uploading file')
    # Write file to Error Logs folder
    f = drive.CreateFile({"title": date_file, "parents": [{"kind": "drive#fileLink", "id": folderID}]})
    f.SetContentFile(BASE_LOG_DIR + '/' + date_file)
    f.Upload()

def main():
    log_info('bootup', data=git_tag())

    global DRIVE_AUTH
    DRIVE_AUTH = google_auth()

    # TO-DO: Check if threshold file is created or set default threshold
    global OPEN_DOOR_DISTANCE_CM
    OPEN_DOOR_DISTANCE_CM = set_threshold()
    print('Threshold set to {} cm'.format(OPEN_DOOR_DISTANCE_CM))

    global RASPI_SERIAL_NUM
    RASPI_SERIAL_NUM = get_serial()

    setup_gpio()
    firebase_connection = get_firebase_connection()
    
    previous_door_state = get_door_state_from_str(get_status(firebase_connection))
    if not previous_door_state:
        previous_door_state = DoorState.unknown

    while True:
        # Upload log file at 01:00-01:01
        if datetime.datetime.now().hour == 1 and datetime.datetime.now().minute < 2:
            upload_log_file(DRIVE_AUTH)

        command = get_command(firebase_connection)
        if command:
            process_command(firebase_connection, command)

        current_door_state = check_door_status()
        if current_door_state != previous_door_state:
            previous_door_state = current_door_state
            update_status(firebase_connection, current_door_state)
            notify_users(firebase_connection, current_door_state)

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
