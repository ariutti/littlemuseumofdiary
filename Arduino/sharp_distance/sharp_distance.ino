#define SHARP A0
float voltage = 0.0;

// filter stuff nad variables
float filtered = 0.0;
float A = 0.1;
float B;

void setup() {
  Serial.begin(9600);
  B = 1.0 - A;
}

void loop() {
  float raw = analogRead( SHARP );
  // 5V / 1024 steps = 4,9mV per step (circa)
  voltage = raw * 0.0049; // Volts;
  
  //value = value * 0.5 + prevValue * 0.5;
  //prevValue = value;

  filtered=A*raw + B*filtered;
  
  //Serial.print( raw );Serial.println("\t");
  //Serial.print( voltage );Serial.println("\t");
  Serial.print( filtered );Serial.println("\t");
  delay(50);

}
