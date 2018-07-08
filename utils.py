import datetime
import os
import subprocess

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

ERROR_DIR = '/home/pi/log_files/errors'
SENSOR_READINGS_DIR = '/home/pi/log_files/sensor_readings'
USAGE_DIR = 'home/pi/log_files/usage'

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

def get_cpu_temperature():
    # Move to the project path.
    project_path = os.path.realpath(os.path.dirname(__file__))
    os.chdir(project_path)

    try:
        raw_output = subprocess.check_output('/opt/vc/bin/vcgencmd measure_temp'.split())
    except BaseException as e:
        return e

    output = raw_output.decode('ascii').strip()

    return output.split('=')[-1]

def print_with_timestamp(msg):
    print('{} - {}'.format(datetime.datetime.now(), msg))

def log_error(group: str, data=None):
    # Make sure the ERROR_DIR exists
    if not os.path.isdir(ERROR_DIR):
        os.mkdir(ERROR_DIR)

    current_time = datetime.datetime.now().strftime('%H_%M_%S')
    current_date = datetime.date.today().strftime('%Y_%m_%d')
    cpu_temperature = get_cpu_temperature()
    file_path = '{}/{}.txt'.format(ERROR_DIR, current_date)
    with open(file_path, 'a') as error_file:
        # Write the message and the exception to that file.
        error_file.write('{} | {} | {} | {}\n'.format(current_time, cpu_temperature, group, data))

def log_sensor_reading(sensor_reading, door_state: str):
    # Make sure the USAGE_DIR exists
    if not os.path.isdir(SENSOR_READINGS_DIR):
        os.mkdir(SENSOR_READINGS_DIR)

    current_time = datetime.datetime.now().strftime('%H_%M_%S')
    current_date = datetime.date.today().strftime('%Y_%m_%d')
    cpu_temperature = get_cpu_temperature()

    file_path = '{}/{}.txt'.format(SENSOR_READINGS_DIR, current_date)
    with open(file_path, 'a') as reading_file:
        reading_file.write('{} | {} | {} cm | {}\n'.format(current_time, cpu_temperature, sensor_reading, door_state))

def log_usage(command: str):
    # Make sure the USAGE_DIR exists
    if not os.path.isdir(USAGE_DIR):
        os.mkdir(USAGE_DIR)

    current_time = datetime.datetime.now().strftime('%H_%M_%S')
    current_date = datetime.date.today().strftime('%Y_%m_%d')
    cpu_temperature = get_cpu_temperature()

    file_path = '{}/{}.txt'.format(USAGE_DIR, current_date)
    with open(file_path, 'a') as usage_file:
        usage_file.write('{} | {} | {}\n'.format(current_time, cpu_temperature, command))

def google_auth():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)

    return drive

def upload_log_files(drive, admin_call=False):
    raspi_id = get_serial()
    # Verify RasPi serial number folder exists on Google Drive
    folder_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    masterFolder = None
    for f in folder_list:
        if f['title'] == raspi_id + ' - Log Files':
            masterFolder = f['id']

    if not masterFolder:
        folder = drive.CreateFile({'title': raspi_id + ' - Log Files', 'mimeType' : 'application/vnd.google-apps.folder'})
        folder.Upload()
        masterFolder = folder['id']

    dir_list = {'Error Logs': ERROR_DIR, 'Sensor Reading Logs': SENSOR_READINGS_DIR, 'Usage Logs': USAGE_DIR}

    # Upload today's log files
    if admin_call:
        upload_file = datetime.datetime.now().strftime('%Y_%m_%d') + '.txt'
        delete_file = None
    # Upload yesterday's log files
    else:
        upload_file = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(1), '%Y_%m_%d') + '.txt'
        delete_file = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(8), '%Y_%m_%d') + '.txt'
    
    for key in dir_list.keys():
        if upload_file in os.listdir(dir_list[key]):
            driveID = {'q': "'{}' in parents and trashed=false".format(masterFolder)}
            folder_list = drive.ListFile(driveID).GetList()
            sub_folder = None
            for f in folder_list:
                if f['title'] == key:
                    sub_folder = f['id']

            if not sub_folder:
                folder = drive.CreateFile({'title': key, 'mimeType' : 'application/vnd.google-apps.folder'})
                folder.Upload()
                sub_folder = folder['id']
            else:
                driveID = {'q': "'{}' in parents and trashed=false".format(sub_folder)}
                file_list = drive.ListFile(driveID).GetList()
                for f in file_list:
                    if f['title'] == upload_file:
                        f.Delete()

            f = drive.CreateFile({"title": upload_file, "parents": [{"kind": "drive#fileLink", "id": sub_folder}]})
            f.SetContentFile(dir_list[key] + '/' + upload_file)
            f.Upload()

            if delete_file:
                if delete_file in os.listdir(dir_list[key]):
                    os.remove(dir_list[key] + '/' + delete_file)
