#include<SPI.h>
#include<RF24.h>

// define pins numbers
const int trigPin = 2;
const int echoPin = 3;
RF24 radio(7,8);

// define variables
float duration;
int GaussianDistance;
int sampleCount = 11;

// define functions
double calculateAverage(float array[], int arrayLength){
  double sum;
  for (int i=0; i<arrayLength; i++){
    sum = sum + array[i];
  }

  return sum/arrayLength;
}

void setup() {
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  Serial.begin(9600); // Starts the serial communication

  radio.begin();
  }

double calculate_distance() {
  // Clear the trigPin
  digitalWrite(trigPin, LOW);
  delay(2);

  // Build array of distances
  float distance[sampleCount];
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
  
void loop() {
  // Clear the trigPin
//  digitalWrite(trigPin, LOW);
//  delay(2);
//
//  // Build array of distances
//  int distance[sampleCount];
//  for (int i=0; i<sampleCount; i++){
//    
//    // Sets the trigPin on HIGH state for 10 micro seconds
//    digitalWrite(trigPin, HIGH);
//    delayMicroseconds(10);
//    digitalWrite(trigPin, LOW);
//    
//    // Read the echoPin, return the sound wave travel time in microseconds
//    duration = pulseIn(echoPin, HIGH);
//    
//    // Calculating the distance (cm)
//    distance[i] = duration*0.034/2;
//  }
//
//  double average = calculateAverage(distance, sampleCount);

  double average = calculate_distance();

  Serial.print("Distance: ");
  Serial.println(average);

  delay(1000);
}