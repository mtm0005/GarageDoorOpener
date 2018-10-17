# To upload to ESP8266
# >>ampy put main.py
# Default port is /dev/tty.SLAB_USBtoUART
# This can be changed by...
# >> export AMPY_PORT=~portname~

print("Hello")

import machine
import time

led = machine.Pin(5, machine.Pin.OUT)

while True:
    led.on()
    time.sleep(1.5)
    led.off()
    time.sleep(.1)