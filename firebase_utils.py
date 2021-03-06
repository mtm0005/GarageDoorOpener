from firebase import firebase
import datetime
import pyfcm
import time

import utils

@utils.try_thrice
def get_firebase_connection(url):
    # Get password from secrets.txt (created manually on each device)
    # This is located in firebase under settings>Service accounts> Database secrets
    # You must be logged in as admin, not as rasmcfall
    with open('secrets.txt', 'r') as f:
        password = f.readline().strip()

    authentication = firebase.FirebaseAuthentication(password, 'rasmcfall@gmail.com',
        extra={'id': utils.get_serial()})
    return firebase.FirebaseApplication(url, authentication=authentication)

@utils.try_thrice
def get_command(firebase_connection, raspi_id):
    command = firebase_connection.get('devices/{}/command'.format(raspi_id), None)

    if command:
        # Clear the command field on firebase so that the App knows it has
        # been received.
        firebase_connection.put('devices/{}'.format(raspi_id), 'command', '')
        utils.print_with_timestamp('Received command: {}'.format(command))
    else:
        # Check for admin command
        # This gives user commands precedence of admin commands
        command = firebase_connection.get('admin/command', None)
        if command:
            # Clear the command field to acknowledge that it has been received
            pass

    return command

@utils.try_thrice
def get_status(firebase_connection, raspi_id):
    status = firebase_connection.get('devices/{}/status'.format(raspi_id), None)
    if status == None:
        firebase_connection.put('devices/{}'.format(raspi_id), 'status', '')
        status = ''

    return status

@utils.try_thrice
def update_status(firebase_connection, raspi_id, status):
    firebase_connection.put('devices/{}'.format(raspi_id), 'status', status)

@utils.try_thrice
def notify_users(firebase_connection, raspi_id, api_key, status):
    utils.print_with_timestamp('Sending notification to user')
    push_service = pyfcm.FCMNotification(api_key=api_key)

    utils.log_usage(status)

    # Loop until we get a device ID.
    phone_ids = None
    while not phone_ids:
        phone_ids = firebase_connection.get('devices/{}/phone_IDs'.format(raspi_id), None)
        if not phone_ids:
            time.sleep(1)

    results = []
    for phone in phone_ids.keys():
        if status == 'open':
            status = 'opened'

        timestamp = datetime.datetime.now().strftime('%I:%M %p on %A %b %d, %Y')
        msg = 'Your door was {} at {}'.format(status, timestamp)
        result = push_service.notify_single_device(registration_id=phone,
            message_title='Garage door update', message_body=msg, sound="Default")

        # TO-DO: Try to send notifications multiple times if there is a failure
        if not result['success']:
            utils.print_with_timestamp('notification failed to send')
            utils.log_error('notification-failure', data=result)

        results.append(result)

    return results

