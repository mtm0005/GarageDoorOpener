// Include libraries
#include<SPI.h>
#include<RF24.h>

// Define pin locations
const int trigPin = 2;
const int echoPin = 3;
const int garageDoorOpener = 5;
RF24 radio(7, 8);

// Define variables)(ation;
long duration;
int sampleCount = 10;
int garageDoorThreshold = 75;

// -------------------- Function Definitions ---------------------------
// Calculate average
float calculateAverage(int array[], int arrayLength){
  float sum;
  for (int i=0; i<arrayLength; i++){
    sum = sum + array[i];
  }

  return sum/arrayLength;
}

float calculate_distance() {
  // Clear the trigPin
  digitalWrite(trigPin, LOW);
  delay(2);

  // Build array of distances
  int distance[sampleCount];
  for (int i=0; i<sampleCount; i++){
    
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

// Determine garage door status
// Returns true if garage door is closed
bool isGarageDoorClosed(){
  Serial.println("Entering isGarageDoorClosed");

  float average = calculate_distance();
  
  Serial.print("Average distance: ");
  Serial.println(average);
  if (average > garageDoorThreshold){
    Serial.println("Average distance is above threshold");
    // Return true if garage door is closed
    return false;
  }

  Serial.println("Average distance is below threshold");
  return true;
  
}

// Toggles the status of the garage door
bool toggleGarageDoor(){
  // Execute garage door command
  digitalWrite(garageDoorOpener, HIGH);
  delay(250);
  digitalWrite(garageDoorOpener, LOW);
  // Return true if command was executed properly
  return true;
}

// --------------------------- Main ---------------------------

void setup(){
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  pinMode(garageDoorOpener, OUTPUT);
  Serial.begin(9600); // Starts the serial communication

  while(!Serial);
  Serial.begin(9600);

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

  // LED test
  for (int i=0; i<4; i++){
    digitalWrite(garageDoorOpener, HIGH);
    delay(250);
    digitalWrite(garageDoorOpener, LOW);
    delay(250);
  }
}

void loop(){
  radio.startListening();

  Serial.println("Listening...");
  
  char receivedMessage[32] = {0};
  if(radio.available()){
    radio.stopListening();
    radio.read(receivedMessage, sizeof(receivedMessage));
    
    Serial.println("Message Received!!!");

    String stringMessage(receivedMessage);

    if(stringMessage == "OpenDoor"){
      Serial.println("OpenDoor command received");
      const char text[] = "OpenDoor command Received";
      radio.write(text, sizeof(text));

      if (isGarageDoorClosed()){
        bool toggleResult = toggleGarageDoor();
        Serial.println("Garage door determined to be close");
        Serial.println("toggleGarageDoor function called");
        Serial.println("Delay for 5 seconds");
        delay(5000); // Delay time for garage door to open/close
        if (!isGarageDoorClosed()){
          Serial.println("Garage door opened successfully");
          //const char text[] = "Garage dooor opened successfully";
          //radio.write(text, sizeof(text));
        }
        else{
          Serial.println("Command Failed");
          //const char text[] = "Command Failed";
          //radio.write(text, sizeof(text));
        }
      }
      else{
        Serial.println("Garage door is already open");
      }
    }
    else if(stringMessage == "CloseDoor"){
      Serial.println("CloseDoor command received");
      const char text[] = "CloseDoor command received";
      radio.write(text, sizeof(text));
      
      if (!isGarageDoorClosed()){
        bool toggleResult = toggleGarageDoor();
        delay(5000);
        if (isGarageDoorClosed()){
          Serial.println("Garage door closed successfully");
          //const char text[] = "Garage dooor closed successfully";
          //radio.write(text, sizeof(text));
        }
        else{
          Serial.println("Command Failed");
          //const char text[] = "Command Failed";
          //radio.write(text, sizeof(text));
        }
      }
      else{
        Serial.println("Garage door is already closed");
      }
    }
    else if (stringMessage == "CheckDoorStatus"){
      Serial.println("CheckDoorStatus command received");
      const char text[] = "CheckDoorStatus command received";
      radio.write(text, sizeof(text));

      if (isGarageDoorClosed()){
        Serial.println("Garage door is currently closed");
        //const char text[] = "Closed";
        //radio.write(text, sizeof(text));
      }
      else{
        Serial.println("Garage door is currently open");
        //const char text[] = "Open";
        //radio.write(text, sizeof(text));
      }
    }
    else{
      Serial.println("Unknown command received");
      //const char text[] = "Unknown command received";
      //radio.write(text, sizeof(text));
    }
  delay(1000);
  }
  delay(200);
}






