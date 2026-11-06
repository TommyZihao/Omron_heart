// GPIO4 -> LED anode; LED cathode -> 220 ohm to 1k ohm -> GND.
// Serial commands: B = one 80ms pulse; T = five test pulses; 0 = off.
constexpr int LED_PIN = 4;
constexpr int BOARD_LED_PIN = 2;
void setLeds(bool on) {
  digitalWrite(LED_PIN, on ? HIGH : LOW);
  digitalWrite(BOARD_LED_PIN, on ? HIGH : LOW);
}
unsigned long offAt = 0, nextAt = 0;
int pending = 0;
void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BOARD_LED_PIN, OUTPUT);
  setLeds(false);
  Serial.begin(115200);
  Serial.println("READY GPIO4+GPIO2; B=pulse T=test 0=off");
}
void loop() {
  while (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'B') { pending = 1; nextAt = millis(); }
    if (cmd == 'T') { pending = 5; nextAt = millis(); }
    if (cmd == '0') { pending = 0; offAt = 0; setLeds(false); Serial.println("OFF"); }
  }
  unsigned long now = millis();
  if (offAt && (long)(now - offAt) >= 0) { setLeds(false); offAt = 0; }
  if (pending && (long)(now - nextAt) >= 0) {
    setLeds(true); offAt = now + 80; nextAt = now + 700; pending--;
    Serial.println("PULSE GPIO4+GPIO2 80ms");
  }
}
