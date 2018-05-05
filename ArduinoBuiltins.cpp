#include "ArduinoBuiltins.hpp"
#include <iostream>

SerialPort Serial;

// TO-DO: Consider adding a time variable that would increment when delay
//        is called.

// TO-DO: Implement a Pin class.
int pin_states[13] = {-1, -1, -1, -1, -1, -1,
                      -1, -1, -1, -1, -1, -1, -1};
int pin_modes[13] = {-1, -1, -1, -1, -1, -1,
                      -1, -1, -1, -1, -1, -1, -1};

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
    pin_states[pin] = state;
}

int digitalRead(int pin)
{
    std::cout << "Reading pin " << pin << "'s value." << std::endl;
    return pin_states[pin];
}

void pinMode(int pin, int mode)
{
    std::cout << "Setting pin " << pin << " to mode " << mode << std::endl;
    pin_modes[pin] = mode;
}

// Waits for the pin to go to a state (HIGH or LOW). Then starts timing and
// waits for the pin to go the opposite state.
int pulseIn(int pin, int state)
{
    std::cout << "Detecting pulse duration for pin " << pin << ", in state ";
    std::cout << state << std::endl;
    return 0;
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
