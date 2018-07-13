#ifndef ArduinoBuiltins_H
#define ArduinoBuiltins_H

#include <string>
#include <iostream>

typedef std::string String;

// Pin states
#define LOW 0
#define HIGH 1

// Pin modes
#define INPUT 0
#define OUTPUT 1

void delay(int s);
void delayMicroseconds(int ms);
void digitalWrite(int pin, int state);
int digitalRead(int pin);
void pinMode(int pin, int mode);
int pulseIn(int pin, int state);

class SerialPort {
    public:
    SerialPort();
    void begin(int baud_rate);
    template <typename T>
    void print(T msg)
    {
        std::cout << msg;
    }

    template <typename T>
    void println(T msg)
    {
        std::cout << msg << std::endl;
    }

    // Overload ! operator
    bool operator!();

    bool active;

    private:
    
    int baud_rate;
};

extern SerialPort Serial;
#endif
