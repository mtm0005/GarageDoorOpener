arduino_sim: arduino_sim.o Master.o ArduinoBuiltins.o ArduinoPin.o RF24_emulator.o
	g++ arduino_sim.o Master.o ArduinoBuiltins.o ArduinoPin.o RF24_emulator.o -o arduino_sim

arduino_sim.o: arduino_sim.cpp
	g++ -c arduino_sim.cpp

Master.o: Master.cpp Master.hpp Master.ino
	g++ -c Master.cpp

Master.cpp: Master.ino
	python3 copy_file.py Master.ino Master.cpp

ArduinoBuiltins.o: ArduinoBuiltins.cpp ArduinoBuiltins.hpp
	g++ -c ArduinoBuiltins.cpp

ArduinoPin.o: ArduinoPin.cpp ArduinoPin.hpp
	g++ -c ArduinoPin.cpp

RF24_emulator.o: RF24_emulator.cpp RF24_emulator.hpp
	g++ -c RF24_emulator.cpp

.PHONY: clean
clean:
	rm *.o Master.cpp arduino_sim