#ifndef ArduinoPin_H
#define ArduinoPin_H

class ArduinoPin {
    public:
    ArduinoPin();
    int pulseIn(int state);
    int digitalRead();
    void digitalWrite(int state);
    void pinMode(int mode);

    private:
    static int num_pins_created;
    int pin_number;
    int state;
    int mode;
};

#endif
