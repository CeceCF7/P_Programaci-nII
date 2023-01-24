#include <Servo.h>. 

const int trigPin = 8;
const int echoPin = 9;

long duration;
int distance;

Servo myServo1;
Servo myServo2;  

void setup() {
  pinMode(trigPin, OUTPUT); 
  pinMode(echoPin, INPUT);
  Serial.begin(9600);
  myServo1.attach(4);
  myServo2.attach(7);  
}

void loop() {

  //posicion incial del servo 2
  myServo2.write(0);

  //movimiento horizontal del servo 1
  for(int i=15;i<=165;i++){  
  myServo1.write(i);
  delay(30);
  distance = calculateDistance();
  Serial.print(i); 
  Serial.print(","); 
  Serial.print(distance); 
  Serial.print("."); 
  }
  
  // movimiento vertical del servo 2
  for(int i=0;i<=30;i++){  
  myServo2.write(i);
  delay(30);
  }

  // repetición
  for(int i=165;i>15;i--){  
  myServo1.write(i);
  delay(30);
  distance = calculateDistance();
  Serial.print(i);
  Serial.print(",");
  Serial.print(distance);
  Serial.print(".");
  }

  // repetición
  for(int i=30;i<=60;i++){  
  myServo2.write(i);
  delay(30);
  }

  // repetición
  for(int i=15;i<=165;i++){  
  myServo1.write(i);
  delay(30);
  distance = calculateDistance();
  
  Serial.print(i); 
  Serial.print(","); 
  Serial.print(distance); 
  Serial.print("."); 
  }

  //repetición
  for(int i=60;i>=30;i--){
  myServo2.write(i);
  delay(30);
  }

  // repetición
  for(int i=165;i>15;i--){  
  myServo1.write(i);
  delay(30);
  distance = calculateDistance();
  Serial.print(i);
  Serial.print(",");
  Serial.print(distance);
  Serial.print(".");
  }

  // repetición
  for(int i=30;i>=0;i--){  
  myServo2.write(i);
  delay(30);
  }

}

int calculateDistance(){ 
  
  digitalWrite(trigPin, LOW); 
  delayMicroseconds(2);
  
  digitalWrite(trigPin, HIGH); 
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH); 
  distance= duration*0.034/2;
  return distance;
}