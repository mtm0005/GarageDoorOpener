// Include libraries
#ifdef ARDUINO
#include<SPI.h>
#include<RF24.h>
#else
#include "Master.hpp"
#include "RF24_emulator.hpp"
#include "ArduinoBuiltins.hpp"
#endif

#include <stdlib.h>

// Define global variables
// Define pins
const int trigPin = 2;
const int echoPin = 3;
const int garageDoorOpener = 5;
RF24 radio(7, 8);

unsigned long startTime;

// Number of samples used to check door status
int sampleCount = 10;

// Garage door status threshold. Below this value represents a close door and
// above this value represents an open door.
int garageDoorThreshold = 130;

// Amount of time it takes for the door to close/open in ms
int garageDelay = 15000;

// Times to try toggleGarageDoor
const int ITERATIONATTEMPTS = 3;
const int ARDUINORESETTIMER = 1000*60*5;
const String OPENDOOR = "openDoor";
const String CLOSEDOOR = "closeDoor";
const String CHECKSTATUS = "checkStatus";
const String SUCCESS = "success";
const String FAILURE = "failure";
const String ACK = "ack";

struct Command {
    String name;
    String value;
    int ID;
    // TO-DO
    // add command.variable
};


// --------------------- Function Definitions ------------------------

// Define reset function for Arduino reset
void(* resetFunc) (void) = 0;

double calculateAverage(float array[], int arrayLength) {
    // Calculate the average of a given array
    double sum;
    for (int i=0; i<arrayLength; i++) {
        sum = sum + array[i];
    }

    return sum/arrayLength;
}

double calculateDistance() {
    // Clear the trigPin
    digitalWrite(trigPin, LOW);
    delay(2);

    float distance[sampleCount];
    float duration;
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

bool isGarageDoorClosed() {
    // Check the current status of the grage door
    // true indicates a closed door

    float average = calculateDistance();

    
    Serial.print("Average distance: ");
    Serial.print(average);
    Serial.print(" compared to ");
    Serial.println(garageDoorThreshold);
    
    if (average > garageDoorThreshold) {
        // A distance larger than the threshold signifies an open door
        Serial.println("Garage door determined to be open");
        return false;
    }

    // Otherwise, the door is closed
    Serial.println("Garage door determined to be closed");
    return true;  
}

void toggleGarageDoor() {
    // Execute garage door command
    digitalWrite(garageDoorOpener, HIGH);
    delay(250);
    digitalWrite(garageDoorOpener, LOW);

    // Return true if command was executed properly
    // Note that this does not signify a successful open/close
}

bool garageDoorCommand(String desiredStatus) {
    // returns true if the garageDoorCommand was executed successfully
    for (int i=0; i<ITERATIONATTEMPTS; i++) {

        if (i>0) {
            Serial.print("toggleGarageDoor: iteration ");
            Serial.println(i+1);
        }

        toggleGarageDoor();
        
        delay(garageDelay);

        if (desiredStatus == OPENDOOR && !isGarageDoorClosed()) {
            Serial.println("garageDoorCommand succeeded");
            return true;
        }
        else if (desiredStatus == CLOSEDOOR && isGarageDoorClosed()) {
            Serial.println("garageDoorCommand succeeded");
            return true;
        }
    }
    Serial.println("garageDoorCommand exceeded max attempts");
    return false;
}

struct Command readMessage() {
    char receivedMessage[32] = {0};
    radio.stopListening();
    radio.read(receivedMessage, sizeof(receivedMessage));

    String tokens[3] = {"", "", ""};
    char* token = strtok(receivedMessage, ",");

    for (int i = 0; i < 3; i++) {
        if (token == NULL) {
            break;
        }
        String item(token);
        tokens[i] = item;
        token = strtok(NULL, ",");
    }

    Command command;

    // Reject messages that aren't in the proper form.
    if (tokens[0] == "" || tokens[1] == "") {
        command.name = "INVALID";
        command.ID = -1;
        return command;
    }

    command.name = tokens[0];
    #ifdef ARDUINO
    command.ID = tokens[1].toInt();
    #else
    command.ID = std::stoi(tokens[1]);
    #endif
    command.value = tokens[2];

    // TO-DO
    // Add ability to parse command.variable

    Serial.println("Command: ");
    Serial.print("    name: ");
    Serial.println(command.name);
    Serial.print("    ID: ");
    Serial.println(command.ID);
    Serial.print("    value: ");
    Serial.println(command.value);

    return command;
}

void sendMessage(String command, int ID, String message) {

    // TO-DO
    // Add ability to send command.variable

    String idString;
    #ifdef ARDUINO
    idString = String(ID);
    #else
    idString = std::to_string(ID);
    #endif
    String response = command + ", " + idString + ", " + message;
    bool sendSuccess = radio.write(response.c_str(), strlen(response.c_str()));
    if (sendSuccess) {
        Serial.println("Response sent: ");
        Serial.println(response);
    }
    else {
        Serial.println("Response NOT sent");
    }
}


void handleCommand(Command command) {
    sendMessage(command.name, command.ID, ACK);
    String value;
    if (command.name == OPENDOOR) {
        // openDoor command received
        if (isGarageDoorClosed()) {
            // Open door
            if (garageDoorCommand(command.name)) {
                value = SUCCESS;
            }
            else {
                value = FAILURE;
            }
        }
        else {
            // Door is already open
            Serial.println("Door was already open");
            value = SUCCESS;
        }
    }
    else if (command.name == CLOSEDOOR) {
        // closeDoor command received
        if (!isGarageDoorClosed()) {
            // Close door
            if (garageDoorCommand(command.name)) {
                value = SUCCESS;
            }
            else {
                value = FAILURE;
            }
        }
        else {
            // Door is already closed
            Serial.println("Door was already closed");
            value = SUCCESS;
        }
    }
    else if (command.name == CHECKSTATUS) {
        // checkDoorStatus command received
        Serial.println("checkStatus command received");
        if (isGarageDoorClosed()) {
            // Garage door is closed
            value = "closed";
        }
        else {
            // Garage door is open
            value = "open";
        }
    }

    // TO-DO
    // Add ability to catch "set" commands

    // TO-DO
    // Add ability to catch "calibrate" commands

    else {
        // Invalid command received
        Serial.println("Unknown message received");
        value = "unknown message";
    }

    // TO-DO
    // add sendMessage ability to send command.variable.

    sendMessage(command.name, command.ID, value);
}

// ----------------------- Setup ----------------------------

void setup() {
    pinMode(trigPin, OUTPUT); // Set the trigPin as an output
    pinMode(garageDoorOpener, OUTPUT); // Set the garageDoorOpener pin as an output
    pinMode(echoPin, INPUT); // Setsthe echoPin as an input

    Serial.begin(9600);
    while(!Serial);

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

    Serial.println("Arduino ready");

    radio.startListening();

    // Initialize startTime
    startTime = millis();
}

void loop() {
    
    if (radio.available()) {
        Serial.println("-------------------------------");
        Serial.println("Message received");
        handleCommand(readMessage());

        radio.startListening();
        // Reset timer startTime
        startTime = millis();
    }
    // If time without message exceeds ARDUINORESETTIMER
    else if (millis() - startTime > ARDUINORESETTIMER) {

        Serial.println("Arduino will reset in...");
        delay(1000);
        Serial.println("3..");
        delay(1000);
        Serial.println("2..");
        delay(1000);
        Serial.println("1..");
        delay(1000);

        resetFunc();
    }
}