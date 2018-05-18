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

PASSWORD = 'rasmcfall1981'
SENDING_EMAIL = 'rasmcfall@gmail.com'
RECV_EMAIL = 'mtm0005@gmail.com'
MAX_CONNECTION_FAILURES = 3

num_open_cmds = 0
num_close_cmds = 0
num_check_cmds = 0

def get_mailbox(email_address, password, server='imap.gmail.com'):
    mail = imaplib.IMAP4_SSL(server)
    mail.login(email_address, password)
    mail.select('inbox')
    return mail

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

# Doesn't work if you send messages from computer. Use phone instead.
def get_commands(mailbox):
    search_criteria = 'UNSEEN FROM mtm0005@gmail.com SUBJECT GarageDoor'
    status, data = mailbox.search(None, search_criteria)
    mail_ids = data[0]

    email_messages = []
    if status == 'OK':
        for mail_id in mail_ids.split():
            print('mail_id: {}'.format(mail_id))
            print('type(mail_id): {}'.format(type(mail_id)))
            status, raw_email_data = mailbox.fetch(mail_id, 'RFC822')
            email_messages.append(email.message_from_bytes(raw_email_data[0][1]))
    else:
        sys.exit('Error trying to read email')

    print('Read {} emails'.format(len(email_messages)))
    commands = []
    for msg in email_messages:
        print('payload: {}'.format(msg.get_payload()))
        print('type(payload): {}'.format(type(msg.get_payload())))
        commands.append(msg.get_payload().strip())
    
    return commands

def send_email(msg: str, subject='Garage door update'):
    email_msg = MIMEText(msg)
    email_msg['Subject'] = subject
    email_msg['From'] = SENDING_EMAIL
    email_msg['To'] = RECV_EMAIL

    try:
        server = smtplib.SMTP_SSL('imap.gmail.com')
        server.login(SENDING_EMAIL, PASSWORD)
        server.sendmail(SENDING_EMAIL, [RECV_EMAIL], email_msg.as_string())
        server.quit()
    except:
        print('Error: Failed to send email ({})'.format(msg))
        with open('sending_errors.txt', 'a') as error_file:
            error_file.write('Exception was triggered while sending mail\n')
            error_file.write(str(sys.exc_info()[0]))
            error_file.write('\n-----------------------------------------\n')

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


def get_for_response(radio, timeout=5.0):
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
        response = get_for_response(radio)
        print('Received response: {}'.format(response))
    else:
        response = ack

    # Email response back to the user.

    status = ''

    if response:
        status = response.split(',')[2]

    if update_user:
        send_email(status)

    return status.strip()

def open_door(mailbox, radio):
    global num_open_cmds
    ack = send_arduino_command(radio, 'openDoor, 1{}'.format(num_open_cmds))
    num_open_cmds += 1
    print('Received ack: {}'.format(ack))
    response = get_for_response(radio, timeout=45.0)
    print('Received response: {}'.format(response))

def close_door(mailbox, radio):
    global num_close_cmds
    ack = send_arduino_command(radio, 'closeDoor, 2{}'.format(num_close_cmds))
    num_close_cmds += 1
    print('Received ack: {}'.format(ack))
    response = get_for_response(radio, timeout=45.0)
    print('Received response: {}'.format(response))

def process_command(command, mailbox, radio):
    print('Processing command: {}'.format(command))
    if command == 'CheckDoorStatus':
        check_door_status(mailbox, radio)
    elif command == 'OpenDoor':
        open_door(mailbox, radio)
    elif command == 'CloseDoor':
        close_door(mailbox, radio)
    else:
        print('Recieved invalid command: {}'.format(command))

def main():
    print('Setting up mailbox')
    mailbox = get_mailbox('rasmcfall@gmail.com', PASSWORD)
    print('Setting up radio')
    radio = get_radio()
    exception_counter = 0
    previous_door_status = ''

    while True:
        print(str(datetime.datetime.now())) 
        try:
            mailbox.select('inbox')
        except:
            print('Handling execption........')
            exception_counter += 1
            with open('errors.txt', 'a') as error_file:
                error_file.write('Exception was triggered while selecting mailbox\n')
                error_file.write(str(sys.exc_info()[0]))
                error_file.write('\n-----------------------------------------\n')
            if exception_counter > 3:
                sys.exit('Closing program. Too many exceptions occurred')
            elif exception_counter == 2:
                msg = 'Attempting to log into email acount again...\n'
                print(msg)
                error_file.write(msg)
                mailbox = get_mailbox('rasmcfall@gmail.com', PASSWORD)
                continue
            else:
                time.sleep(5)
                continue

        try:
            print('Looking for commands...')
            commands = get_commands(mailbox)
        except:
            print('Handling execption........')
            exception_counter += 1
            with open('errors.txt', 'a') as error_file:
                error_file.write('Exception was triggered during get_commands\n')
                error_file.write(str(sys.exc_info()[0]))
                error_file.write('\n-----------------------------------------\n')
            if exception_counter > 2:
                sys.exit('Closing program. Too many exceptions occurred')
            else:
                continue
                
        print('Received {} commands: {}'.format(len(commands), commands))

        # Parse commands and execute commands
        for command in commands:
            process_command(command, mailbox, radio)

        # Get the current door status
        current_door_status = ''
        max_attempts = 3
        num_attempts = 0
        while ((not current_door_status) and (num_attempts < max_attempts)):
            num_attempts += 1
            current_door_status = check_door_status(mailbox, radio, update_user=False)
        msg = ''

        if current_door_status == 'open' and previous_door_status == 'closed':
            msg = 'Door was opened at {}'.format(datetime.datetime.now())
        elif current_door_status == 'closed' and previous_door_status == 'open':
            msg = 'Door was closed at {}'.format(datetime.datetime.now())
        elif num_attempts >= max_attempts:
            msg = 'Raspi is having trouble getting garage door status.'

        if msg:
            send_email(msg, subject='Garage door alert!')

        previous_door_status = current_door_status

        print('-----------------------------------------\n')
        time.sleep(10)

main()
