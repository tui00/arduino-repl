#include <Arduino.h>
#include "config.h"
#include "soft_pwm.h"
#include "commands.h"

byte commandBuffer[BUFFER_SIZE];
int bufferIndex = 0;
unsigned long startTime;

void setup() {
    Serial.begin(BOUDRATE);
    startTime = millis();
    softPWMCount = 0;
}

void loop() {
    updateSoftPWM();

    while (Serial.available() && bufferIndex < BUFFER_SIZE) {
        commandBuffer[bufferIndex++] = Serial.read();
    }

    if (hasCompleteCommand()) {
        executeBufferedCommand();
        sendResponse();

        byte command = commandBuffer[0];
        int commandLength = 1 + getRequiredArgs(command);

        for (int i = commandLength; i < bufferIndex; i++) {
            commandBuffer[i - commandLength] = commandBuffer[i];
        }
        bufferIndex -= commandLength;
    }
}
