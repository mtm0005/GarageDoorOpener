#include "ArduinoPin.hpp"
#include <iostream>

int ArduinoPin::num_pins_created = 0;

ArduinoPin::ArduinoPin()
{
    std::cout << "Initializing ArduinoPin " << num_pins_created << std::endl;
    this->pin_number = num_pins_created;
    num_pins_created++;
}

int ArduinoPin::pulseIn(int state)
{
    std::cout << "PIN " << this->pin_number << ": pulseIn()" << std::endl;
    return this->pin_number;
}

int ArduinoPin::digitalRead()
{
    std::cout << "PIN " << this->pin_number << ": digitalRead" << std::endl;
    return this->state;
}

void ArduinoPin::digitalWrite(int state)
{
    std::cout << "PIN " << this->pin_number << ": digitalWrite()" << std::endl;
    this->state = state;
}

void ArduinoPin::pinMode(int mode)
{
    std::cout << "PIN " << this->pin_number << ": pinMode()" << std::endl;
    this->mode = mode;
}
