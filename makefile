arduino_sim: Master.o ArduinoBuiltins.o RF24_emulator.o
	g++ Master.o ArduinoBuiltins.o RF24_emulator.o -o arduino_sim

Master.o: Master.cpp
	g++ -c Master.cpp

ArduinoBuiltins.o: ArduinoBuiltins.cpp ArduinoBuiltins.hpp
	g++ -c ArduinoBuiltins.cpp

RF24_emulator.o: RF24_emulator.cpp RF24_emulator.hpp
	g++ -c RF24_emulator.cpp

clean:
	rm *.o arduino_sim