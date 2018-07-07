import datetime
import os
import subprocess

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

BASE_LOG_DIR = '/home/pi/log_files'

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

def log_info(group: str, data=None):
    # Make sure the BASE_LOG_DIR exists
    if not os.path.isdir(BASE_LOG_DIR):
        os.mkdir(BASE_LOG_DIR)

    current_time = datetime.datetime.now().strftime('%H_%M_%S')
    current_date = datetime.date.today().strftime('%Y_%m_%d')
    cpu_temperature = get_cpu_temperature()
    file_path = '{}/{}.txt'.format(BASE_LOG_DIR, current_date)
    with open(file_path, 'a') as log_file:
        # Write the message and the exception to that file.
        log_file.write('{} | {} | {} | {}\n'.format(current_time, cpu_temperature, group, data))

def google_auth():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)

    return drive

def upload_log_file(drive, raspi_id, day='yesterday'):    
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
        if f['title'] == raspi_id + ' - Error Logs':
            folderID = f['id']
    
    # Create Error Logs folder if it doesn't exist
    if not folderID:
        print('Creating Google folder')
        folder = drive.CreateFile({'title': raspi_id + ' - Error Logs', 'mimeType' : 'application/vnd.google-apps.folder'})
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
