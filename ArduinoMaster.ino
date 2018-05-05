// Include libraries
#include<SPI.h>
#include<RF24.h>

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
int timeout = 3;                // Times to try garageDoorRemote


// --------------------- Function Definitions ------------------------

float calculateAverage(int array[], int arrayLength){
    // Calculate the average of a given array
    float sum;
    for (int i=0; i<arrayLength; i++){
    sum = sum + array[i];
}

float calculateDistance(){
    // Clear the trigPin
    digitalWrite(trigPin, LOW);
    delay(2);

    int distance[sampleCount];
    long duration
    for (int i=0; i<sampleCount; i++){
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

char isGarageDoorClosed(){
    // Check the current status of the grage door
    // true indicates a closed door

    float average = calculateDistance();
    
    if (average > garageDoorThreshold){
        // A distance larger than the threshold signifies a clsoed door
        return true;
    }

    // Otherwise, the door is open
    return false;  
}

void garageDoorRemote(){
    // Execute garage door command
    digitalWrite(garageDoorOpener, HIGH);
    delay(250);
    digitalWrite(garageDoorOpener, LOW);

    // Return true if command was executed properly
    // Note that this does not signify a successful open/close
}

bool garageDoorCommand(char desiredStatus){
    // returns true if the garageDoorCommand was executed successfully
    for (int i=0; i<timeout; i++){
        garageDoorRemote();
        
        delay(garageDelay);

        if (desiredStatus == "open" && !isGarageDoorClosed()){
            return true;
        }
        else if (desiredStatus == "closed" && isGarageDoorClosed()){
            return true;
        }
        // Should be put another delay here? 
        // What are the circumstances for this?
    }

    return false;
}

char readMessage(){
    radio.stopListening();
    radio.read(receivedMessage, sizeof(receivedMessage));
    
    return stringMessage(receivedMessage);
}

void sendMessage(char command, int ID, char message){
    //send message
}

// ----------------------- Setup ----------------------------

void setup(){
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

void loop(){
    radio.startListening();

    char receivedMessage[32] = {0};
    if (radio.available()){

        sendMessage(receivedMessage(), 999, "ack");
        if (receivedMessage() == "openDoor"){
            // openDoor command received
            if (isGarageDoorClosed()){
                // open door
                if (garageDoorCommand("open")){
                    sendMessage("openDoor", 999, "open");
                }
            }
            else{
                // Door is already open
                sendMessage("openDoor", 999, "open");
            }
        }
        else if (receivedMessage() == closeDoor){
            // closeDoor command received
            if (!isGarageDoorClosed()){
                // close door
                if (garageDoorCommand("closed")){
                    sendMessage("closeDoor", 999, "closed");
                }
            }
            else{
                // door is already closed
                sendMessage("closeDoor", 999, "closed");
            }
        }
        else if (receivedMessage() == "checkDoorStatus"){
            // checkDoorStatus command received
            if (isGarageDoorClosed()){
                // Garage door is closed
                sendMessage("checkDoorStatus", 999, "closed");
            }
            else{
                // Garage door is open
                sendMessage("checkDoorStatus", 999, "open");
            }
        }
        else{
            // Invalid command received
            sendMessage("Unknown", 999, "Unknown Message");
        }
    }
    delay(100);
}