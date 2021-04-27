int ambPin = A3;

void setup() {
  pinMode(ambPin, INPUT);
  Serial.begin(9600); //9600 bps
}

void loop() {
  int ambVal = analogRead(ambPin) * 0.9765625; //basically sensor returns lux
  Serial.println(ambVal);
  delay(200); //200 ms delay
}
