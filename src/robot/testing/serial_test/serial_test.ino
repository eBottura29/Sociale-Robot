int myValue = 0;

void setup() {
  Serial.begin(9600);
  delay(500); // USB serial settle time
  Serial.println("Board ready");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();  // removes \r and whitespace

    if (cmd.startsWith("SET ")) {
      myValue = cmd.substring(4).toInt();
      Serial.print("Value set to: ");
      Serial.println(myValue);
    }
  }

  delay(10);
}
