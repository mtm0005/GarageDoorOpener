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

bool toggleGarageDoor(){
    // Execute garage door command
    digitalWrite(garageDoorOpener, HIGH);
    delay(250);
    digitalWrite(garageDoorOpener, LOW);

    // Return true if command was executed properly
    // Note that this does not signify a successful open/close
    return true;
}

char readMessage(){
    radio.stopListening();
    radio.read(receivedMessage, sizeof(receivedMessage));
    
    return stringMessage(receivedMessage);
}

bool sendAck(char command, int ID, char ack="ack"){
    //send message
    return true
}

bool sendResult(char command, int ID, char result){
    //send result
    return true
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

        sendAck(receivedMessage(), 999);
        if (receivedMessage() == "openDoor"){
            // openDoor command received
            if (isGarageDoorClosed()){
                // open door
            }
            else{
                // Door is already open
                sendResult("open", 999)
            }
        }
        else if (receivedMessage() == closeDoor){
            // closeDoor command received
            if (!isGarageDoorClosed()){
                // close door
            }
            else{
                // door is already closed
            }
        }
        else if (receivedMessage() == "checkDoorStatus"){
            // checkDoorStatus command received
            if (isGarageDoorClosed()){
                // Garage door is closed
            }
            else{
                // Garage door is open
            }
        }
        else{
            // Invalid command received
        }
    }
}