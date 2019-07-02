#define SHARP A0
float voltage = 0.0;

// filter stuff nad variables
float filtered = 0.0;
float A = 0.07;
float B;

float linearizedDistance = 0.0;
float prevLinearizedDistance = 0.0;

long lastTime = 0;


// SETUP ///////////////////////////////////////////////////////////////////////////////
void setup() {
  Serial.begin(9600);
  Serial.println("\n BEGIN \n");
  B = 1.0 - A;
}

// LOOP ////////////////////////////////////////////////////////////////////////////////
void loop() {
  float raw = analogRead( SHARP );
  // 5V / 1024 steps = 4,9mV per step (circa)
  voltage = raw * 0.0049; // Volts;
  
  //value = value * 0.5 + prevValue * 0.5;
  //prevValue = value;

  filtered=A*raw + B*filtered;
  
  //Serial.print( raw );Serial.println("\t");
  //Serial.print( voltage );Serial.println("\t");
  //Serial.print( filtered );Serial.println("\t");

  // source: https://acroname.com/articles/linearizing-sharp-ranger-data
  if(raw > 0.0 )
  {
    linearizedDistance = (6787.0/(filtered - 3)) - 4;
    //filtered=A*linearizedDistance + B*prevLinearizedDistance;
    //prevLinearizedDistance = filtered;
  }

  //Serial.print( linearizedDistance );Serial.println("\t");

  //Serial.print("[ ");
  if( millis() - lastTime > 1000) {
    Serial.print( raw );Serial.print("\t");
    Serial.print( filtered );Serial.print("\t");
    Serial.print( voltage ); Serial.print("\t");
    Serial.print( linearizedDistance ); Serial.print("\t");
    Serial.println();
    lastTime = millis();
  }
  
  delay(25);
}
