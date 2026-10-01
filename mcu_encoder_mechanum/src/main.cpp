#include <Arduino.h>

const int ena = 2; 
const int enb = 4; 
const int enc = 5;
const int end = 18;

// FR Motor
const int in1 = 12;
const int in2 = 13;

// FL Motor
const int in3 = 14;
const int in4 = 15;

// BR Motor
const int in5 = 16;
const int in6 = 17;

//BL Motor
const int in7 = 19;
const int in8 = 21;

char command;

void setup() {
  pinMode(ena, OUTPUT);
  pinMode(enb, OUTPUT);
  pinMode(enc, OUTPUT);
  pinMode(end, OUTPUT);

  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  pinMode(in5, OUTPUT);
  pinMode(in6, OUTPUT);
  pinMode(in7, OUTPUT);
  pinMode(in8, OUTPUT);
  
  Serial.begin(115200);
}

void forward(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, speed);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  digitalWrite(in5, HIGH);
  digitalWrite(in6, LOW);
  digitalWrite(in7, HIGH);
  digitalWrite(in8, LOW);
}

void backward(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, speed);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  digitalWrite(in5, LOW);
  digitalWrite(in6, HIGH);
  digitalWrite(in7, LOW);
  digitalWrite(in8, HIGH);
}

void left(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, speed);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  digitalWrite(in5, LOW);
  digitalWrite(in6, HIGH);
  digitalWrite(in7, HIGH);
  digitalWrite(in8, LOW);
}

void right(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, speed);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  digitalWrite(in5, HIGH);
  digitalWrite(in6, LOW);
  digitalWrite(in7, LOW);
  digitalWrite(in8, HIGH);
}

void clockwise(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, speed);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  digitalWrite(in5, LOW);
  digitalWrite(in6, HIGH);
  digitalWrite(in7, HIGH);
  digitalWrite(in8, LOW);
}

void counterclockwise(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, speed);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  digitalWrite(in5, HIGH);
  digitalWrite(in6, LOW);
  digitalWrite(in7, LOW);
  digitalWrite(in8, HIGH);
}

void frontleft(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, 0);
  analogWrite(enc, 0);
  analogWrite(end, speed);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  digitalWrite(in5, LOW);
  digitalWrite(in6, LOW);
  digitalWrite(in7, HIGH);
  digitalWrite(in8, LOW);
}

void frontright(int speed){
  analogWrite(ena, 0);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, 0);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  digitalWrite(in5, HIGH);
  digitalWrite(in6, LOW);
  digitalWrite(in7, LOW);
  digitalWrite(in8, LOW);
}

void backleft(int speed){
  analogWrite(ena, 0);
  analogWrite(enb, speed);
  analogWrite(enc, speed);
  analogWrite(end, 0);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  digitalWrite(in5, LOW);
  digitalWrite(in6, HIGH);
  digitalWrite(in7, LOW);
  digitalWrite(in8, LOW);
}

void backright(int speed){
  analogWrite(ena, speed);
  analogWrite(enb, 0);
  analogWrite(enc, 0);
  analogWrite(end, speed);

  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  digitalWrite(in5, LOW);
  digitalWrite(in6, LOW);
  digitalWrite(in7, LOW);
  digitalWrite(in8, HIGH);
}

void stop(){
  analogWrite(ena, 0);
  analogWrite(enb, 0);
  analogWrite(enc, 0);
  analogWrite(end, 0);

  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  digitalWrite(in5, LOW);
  digitalWrite(in6, LOW);
  digitalWrite(in7, LOW);
  digitalWrite(in8, LOW);
}

void loop() {
  command = Serial.read();

}