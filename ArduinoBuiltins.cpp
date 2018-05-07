#include "ArduinoBuiltins.hpp"
#include "ArduinoPin.hpp"
#include <iostream>

SerialPort Serial;

const int NUM_PINS = 14;
ArduinoPin pins[NUM_PINS];

// TO-DO: Consider adding a time variable that would increment when delay
//        is called.

void delay(int s)
{
    std::cout << "delay(" << s << ")" << std::endl;
}

void delayMicroseconds(int ms)
{
    std::cout << "delayMicroseconds(" << ms << ")" << std::endl;
}

void digitalWrite(int pin, int state)
{
    std::cout << "Setting pin " << pin << " to state " << state << std::endl;
    pins[pin].digitalWrite(state);
}

int digitalRead(int pin)
{
    std::cout << "Reading pin " << pin << "'s value." << std::endl;
    return pins[pin].digitalRead();
}

void pinMode(int pin, int mode)
{
    std::cout << "Setting pin " << pin << " to mode " << mode << std::endl;
    pins[pin].pinMode(mode);
}

// Waits for the pin to go to a state (HIGH or LOW). Then starts timing and
// waits for the pin to go the opposite state.
int pulseIn(int pin, int state)
{
    std::cout << "Detecting pulse duration for pin " << pin << ", in state ";
    std::cout << state << std::endl;
    return pins[pin].pulseIn(state);
}

SerialPort::SerialPort()
{
    std::cout << "Initializing a SerialPort." << std::endl;
    this->active = false;
}

void SerialPort::begin(int baud_rate)
{
    std::cout << "SerialPort.begin" << std::endl;
    this->baud_rate = baud_rate;
    this->active = true;
}

bool SerialPort::operator!()
{
    return !this->active;
}
