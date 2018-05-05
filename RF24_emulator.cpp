#include "RF24_emulator.hpp"
#include <iostream>

RF24::RF24(int p, int q) 
{
    std::cout << "p: " << p << ", q: " << q << std::endl;
    this->msg_available = false;
}

void RF24::begin()
{
    std::cout << "begin radio" << std::endl;
}

void RF24::powerUp()
{
    std::cout << "powerUp" << std::endl;
}

void RF24::powerDown()
{
    std::cout << "powerDown" << std::endl;
}

void RF24::startListening()
{
    std::cout << "startListening" << std::endl;
}

void RF24::stopListening()
{
    std::cout << "stopListening" << std::endl;
}

void RF24::setPALevel(int pa_level)
{
    this->pa_level = pa_level;
}

void RF24::setChannel(int channel)
{
    this->channel = channel;
}

void RF24::setDataRate(int data_rate)
{
    this->data_rate = data_rate;
}

void RF24::openWritingPipe(long int pipe)
{
    std::cout << "Opening writing pipe: " << pipe << std::endl;
    this->writing_pipe = pipe;
}

void RF24::openReadingPipe(int i, long int pipe)
{
    std::cout << "Opening reading pipe: " << pipe << std::endl;
    this->reading_pipe = pipe;
}

void RF24::enableDynamicPayloads()
{
    std::cout << "enableDynamicPayloads" << std::endl;
}

void RF24::read(char* msg, unsigned long msg_size)
{
    std::cout << "read" << std::endl;
}

void RF24::write(const char msg[], unsigned long msg_size)
{
    std::cout << "write" << std::endl;
}

bool RF24::available()
{
    std::cout << "available" << std::endl;
    return msg_available;
}
