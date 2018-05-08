// Include libraries
#ifdef ARDUINO
#include<SPI.h>
#include<RF24.h>
#else
#include "Master.hpp"
#include "RF24_emulator.hpp"
#include "ArduinoBuiltins.hpp"
#include <vector>
#include <sstream>
#endif

// Define pins
const int trigPin = 2;
const int echoPin = 3;
const int garageDoorOpener = 5;
RF24 radio(7, 8);

// Define universal variables
int sampleCount = 10; // Number of samples used to check door status
int garageDoorThreshold = 75;   // Garage door status threshold
                                // Above this value represents a close door
                                // Below this value represents an open door
int garageDelay = 15;           // Amount of time it takes for the door to close/open
const int ITERATIONATTEMPTS = 3;                // Times to try garageDoorRemote
const String OPENDOOR = "openDoor";
const String CLOSEDOOR = "closeDoor";
const String CHECKSTATUS = "checkStatus";
const String SUCCESS = "success";
const String FAILURE = "failure";
const String ACK = "ack";

struct Command {
    String name;
    String data;
    int ID;
};


// --------------------- Function Definitions ------------------------

float calculateAverage(int array[], int arrayLength) {
    // Calculate the average of a given array
    float sum;
    for (int i=0; i<arrayLength; i++) {
        sum = sum + array[i];
    }

    return sum/arrayLength;
}

float calculateDistance() {
    // Clear the trigPin
    digitalWrite(trigPin, LOW);
    delay(2);

    int distance[sampleCount];
    long duration;
    for (int i=0; i<sampleCount; i++) {
        // Build an array of sensor measurements

        // Sets the trigPin on HIGH state for 10 micro seconds
        digitalWrite(trigPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin, LOW);
        
        // Read the echoPin, return the sound wave travel time in microseconds
        duration = pulseIn(echoPin, HIGH);
        
        // Calculating the distance (cm)
        distance[i] = duration*0.034/2;
    }

  return calculateAverage(distance, sampleCount);
}

char isGarageDoorClosed() {
    // Check the current status of the grage door
    // true indicates a closed door

    float average = calculateDistance();
    
    if (average > garageDoorThreshold) {
        // A distance larger than the threshold signifies a clsoed door
        return true;
    }

    // Otherwise, the door is open
    return false;  
}

void garageDoorRemote() {
    // Execute garage door command
    digitalWrite(garageDoorOpener, HIGH);
    delay(250);
    digitalWrite(garageDoorOpener, LOW);

    // Return true if command was executed properly
    // Note that this does not signify a successful open/close
}

bool garageDoorCommand(String desiredStatus) {
    // returns true if the garageDoorCommand was executed successfully
    for (int i=0; i<ITERATIONATTEMPTS; i++){
        garageDoorRemote();
        
        delay(garageDelay);

        if (desiredStatus == OPENDOOR && !isGarageDoorClosed()) {
            return true;
        }
        else if (desiredStatus == CLOSEDOOR && isGarageDoorClosed()) {
            return true;
        }
    }

    return false;
}

std::vector<std::string> split(const std::string& s, char delimiter) {
   std::vector<std::string> tokens;
   std::string token;
   std::istringstream tokenStream(s);
   while (std::getline(tokenStream, token, delimiter)) {
      tokens.push_back(token);
   }

   return tokens;
}

struct Command readMessage() {
    char receivedMessage[32] = {0};
    radio.stopListening();
    radio.read(receivedMessage, sizeof(receivedMessage));
    
    String stringMessage(receivedMessage);

    std::vector<std::string> command_vector = split(stringMessage, ',');
    Command command;
    command.name = command_vector[0];
    command.ID = std::stoi(command_vector[1]);
    if (command_vector.size() > 2) {
        command.data = command_vector[2];
    }

    return command;
}

void sendMessage(String command, int ID, String message) {
    String response = command + ", " + std::to_string(ID) + ", " + message;
    radio.write(response.c_str(), sizeof(response.c_str()));
}


void handleCommand(Command command) {
    sendMessage(command.name, command.ID, ACK);
    String result;
    if (command.name == OPENDOOR) {
        // openDoor command received
        if (isGarageDoorClosed()) {
            // Open door
            if (garageDoorCommand(command.name)) {
                result = SUCCESS;
            }
            else {
                result = FAILURE;
            }
        }
        else {
            // Door is already open
            result = SUCCESS;
        }
    }
    else if (command.name == CLOSEDOOR) {
        // closeDoor command received
        if (!isGarageDoorClosed()) {
            // Close door
            if (garageDoorCommand(command.name)) {
                result = SUCCESS;
            }
            else {
                result = FAILURE;
            }
        }
        else {
            // Door is already closed
            result = SUCCESS;
        }
    }
    else if (command.name == CHECKSTATUS) {
        // checkDoorStatus command received
        if (isGarageDoorClosed()) {
            // Garage door is closed
            result = "closed";
        }
        else {
            // Garage door is open
            result = "open";
        }
    }
    else {
        // Invalid command received
        result = "unknown message";
    }

    sendMessage(command.name, command.ID, result);
}

// ----------------------- Setup ----------------------------

void setup() {
    pinMode(trigPin, OUTPUT); // Set the trigPin as an output
    pinMode(garageDoorOpener, OUTPUT); // Set the garageDoorOpener pin as an output
    pinMode(echoPin, INPUT); // Setsthe echoPin as an input

    radio.begin();
    radio.stopListening();
    radio.setPALevel(RF24_PA_MIN);
    radio.setChannel(0x76);
    radio.openWritingPipe(0xF0F0F0F0E1LL);
    const uint64_t pipe = (0xE8E8F0F0E1LL);
    radio.openReadingPipe(1, pipe);

    radio.enableDynamicPayloads();
    radio.setDataRate(RF24_250KBPS);
    radio.powerUp();
}

void loop() {
    delay(100);
    radio.startListening();

    if (radio.available()) {
        handleCommand(readMessage());
    }
}