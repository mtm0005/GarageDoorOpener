#! /usr/local/bin/python3

import datetime
import email
import getpass
import imaplib
import RPi.GPIO as GPIO
import spidev
import smtplib
import sys
import time

from email.mime.text import MIMEText

from lib_nrf24 import NRF24

from firebase import firebase

FIREBASE_URL = 'https://garagedoortest-731f7.firebaseio.com/'

num_open_cmds = 0
num_close_cmds = 0
num_check_cmds = 0

def get_firebase_connection():
    return firebase.FirebaseApplication(FIREBASE_URL)

def get_radio():
    GPIO.setmode(GPIO.BCM)
    pipes = [[0xE8, 0xE8, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]]

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(0, 17)
    # TO-DO: Reset radio (just the line below) if program gets killed.
    radio.stopListening()

    radio.setPayloadSize(32)
    radio.setChannel(0x76)
    radio.setDataRate(NRF24.BR_250KBPS)
    #radio.setDataRate(NRF24.BR_1MBPS)
    radio.setPALevel(NRF24.PA_MIN)

    radio.setAutoAck(True)
    radio.enableDynamicPayloads()
    radio.enableAckPayload()

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1, pipes[1])
    radio.printDetails()
    return radio

def get_command(firebase_connection):
    # TODO: add error handling
    command = firebase_connection.get('command', None)

    # Clear the command field on firebase so that the App
    # knows it has been received.
    firebase_connection.put('', 'command', '')
    return command

def update_status(firebase_connection, msg: str):
    firebase_connection.put('', 'status', msg)

def build_command_from_str(command):
    cmd_msg = list(command)
    while len(cmd_msg) < 32:
        cmd_msg.append(0)
    return cmd_msg

# Returns the response as a string
def send_arduino_command(radio, command, timeout=5.0):
    print('Preparing to send command: {}'.format(command))
    command = build_command_from_str(command)
    start_time = time.time()
    response = ''
    while start_time + timeout >= time.time():
        radio.stopListening()
        print('Sending command: {}'.format(command))
        radio.write(command)
        radio.startListening()
        send_time = time.time()
        while not radio.available():
            time.sleep(0.002)
            if send_time + timeout/10 <= time.time():
                break

        # Read a message if one is available.
        if radio.available():
            raw_response = []
            radio.read(raw_response, radio.getDynamicPayloadSize())
            print('Received: {}'.format(raw_response))
            print('Translating the raw_response into unicode characters')
            for i in raw_response:
                # Decode into standard unicode set
                if i >= 32 and i <= 126:
                    response += chr(i)
            print('Out received message decodes to : {}'.format(response))
            break

    radio.stopListening()

    if not response:
        print('Command, {}, timed out.'.format(command))

    return response


def wait_for_response(radio, timeout=5.0):
    print('Waiting for response...')
    radio.startListening()
    start_time = time.time()
    response = ''
    while not radio.available():
        time.sleep(0.002)
        if start_time + timeout < time.time():
            print('timed out')
            break

    # Read a message if one is available.
    if radio.available():
        raw_response = []
        radio.read(raw_response, radio.getDynamicPayloadSize())
        print('Received: {}'.format(raw_response))
        print('Translating the raw_response into unicode characters')
        for i in raw_response:
            # Decode into standard unicode set
            if i >= 32 and i <= 126:
                response += chr(i)
        print('Out received message decodes to : {}'.format(response))

    radio.stopListening()

    return response
        

def check_door_status(mailbox, radio, update_user=True):
    global num_check_cmds
    ack = send_arduino_command(radio, 'checkStatus, 3{}'.format(num_check_cmds))
    num_check_cmds +=1
    response = ''

    if not ack:
        print('Did not receive ACK')
        return ''

    print('Received ack: {}'.format(ack))

    if ack.split(',')[2].strip() == 'ack':
        response = wait_for_response(radio)
        print('Received response: {}'.format(response))
    else:
        response = ack

    # Email response back to the user.

    status = ''

    if response:
        status = response.split(',')[2]

    if update_user:
        update_status(mailbox, status)

    return status.strip()

def open_door(mailbox, radio):
    global num_open_cmds
    ack = send_arduino_command(radio, 'openDoor, 1{}'.format(num_open_cmds))
    num_open_cmds += 1
    print('Received ack: {}'.format(ack))
    response = wait_for_response(radio, timeout=45.0)
    print('Received response: {}'.format(response))

def close_door(mailbox, radio):
    global num_close_cmds
    ack = send_arduino_command(radio, 'closeDoor, 2{}'.format(num_close_cmds))
    num_close_cmds += 1
    print('Received ack: {}'.format(ack))
    response = wait_for_response(radio, timeout=45.0)
    print('Received response: {}'.format(response))

def process_command(command, mailbox, radio):
    print('Processing command: {}'.format(command))
    if command == 'checkDoorStatus':
        check_door_status(mailbox, radio)
    elif command == 'openDoor':
        open_door(mailbox, radio)
    elif command == 'closeDoor':
        close_door(mailbox, radio)
    else:
        print('Recieved invalid command: {}'.format(command))

def main():
    print('Setting up firebase')
    mailbox = get_firebase_connection()
    print('Setting up radio')
    radio = get_radio()
    exception_counter = 0
    previous_door_status = ''

    while True:
        try:
            print('Looking for commands...')
            commands = get_command(mailbox)
        except:
            print('Handling execption........')
            exception_counter += 1
            with open('errors.txt', 'a') as error_file:
                error_file.write('Exception was triggered during get_command\n')
                error_file.write(str(sys.exc_info()[0]))
                error_file.write('\n-----------------------------------------\n')
            if exception_counter > 2:
                sys.exit('Closing program. Too many exceptions occurred')
            else:
                continue
                
        print('Received {} commands: {}'.format(len(commands), commands))

        # Parse commands and execute commands
        #for command in commands:
        process_command(commands, mailbox, radio)

        # Get the current door status
        current_door_status = ''
        max_attempts = 3
        num_attempts = 0
        while ((not current_door_status) and (num_attempts < max_attempts)):
            num_attempts += 1
            current_door_status = check_door_status(mailbox, radio, update_user=False)
        msg = ''

        if current_door_status == 'open' and previous_door_status == 'closed':
            #msg = 'Door was opened at {}'.format(datetime.datetime.now())
            msg = 'open'
        elif current_door_status == 'closed' and previous_door_status == 'open':
            #msg = 'Door was closed at {}'.format(datetime.datetime.now())
            msg = 'closed'
        elif num_attempts >= max_attempts:
            msg = 'Raspi is having trouble getting garage door status.'

        if msg:
            update_status(mailbox, msg)

        if current_door_status:
            previous_door_status = current_door_status

        print('-----------------------------------------\n')
        time.sleep(5)

main()
