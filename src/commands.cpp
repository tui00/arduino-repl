#include "commands.h"
#include "config.h"
#include "utils.h"
#include <Arduino.h>

extern byte commandBuffer[BUFFER_SIZE];
extern int bufferIndex;
extern SoftPWM softPWM[MAX_SOFT_PWM];
extern byte softPWMCount;

CommandResult result;

int getRequiredArgs(byte command)
{
    switch (command)
    {
    case CMD_NOP:
    case CMD_RESET:
    case CMD_INFO:
        return 0;
    case CMD_PINMODE:
    case CMD_DIGITALWRITE:
    case CMD_ANALOGWRITE:
        return 2;
    case CMD_DIGITALREAD:
    case CMD_ANALOGREAD:
        return 1;
    default:
        return 0;
    }
}

bool hasCompleteCommand()
{
    return bufferIndex > 0 && bufferIndex > getRequiredArgs(commandBuffer[0]);
}

void sendInfo();

void executeBufferedCommand()
{
    result = {false, false, false, 0};
    byte command = commandBuffer[0];
    byte pin = 0;
    bool error = false;

    if (command != CMD_NOP && command != CMD_RESET && command != CMD_INFO)
    {
        pin = readPin(commandBuffer[1], error);
        result.hasError = error;
        if (error)
            return;
    }

    switch (command)
    {
    case CMD_NOP:
        break;
    case CMD_INFO:
        sendInfo();
        result.hasOutput = true;
        break;
    case CMD_DIGITALREAD:
        result.outputValue = digitalRead(pin);
        result.hasOutput = true;
        break;
    case CMD_DIGITALWRITE:
        resetPWM(pin);
        digitalWrite(pin, commandBuffer[2]);
        break;
    case CMD_ANALOGREAD:
        result.outputValue = analogRead(pin);
        result.hasOutput = true;
        result.isTwoByteOutput = true;
        break;
    case CMD_ANALOGWRITE:
        result.hasError = !setPWM(pin, commandBuffer[2]);
        break;
    case CMD_RESET:
        result = {false, false, false, 0};
        sendResponse();
        asm volatile("jmp 0");
        break;
    case CMD_PINMODE:
        pinMode(pin, commandBuffer[2]);
        break;
    default:
        result.hasError = true;
    }
}

void sendResponse()
{
    if (result.hasError)
    {
        Serial.write(ERROR_CODE);
        return;
    }

    if (result.hasOutput)
    {
        Serial.write(result.outputValue & 0xFF);
        if (result.isTwoByteOutput)
            Serial.write((result.outputValue >> 8) & 0xFF);
    }

    Serial.write(SUCCESS_CODE);
}

void sendUInt16(int value)
{
    Serial.write(value & 0xFF);
    Serial.write((value >> 8) & 0xFF);
}

void sendUInt32(unsigned long value)
{
    Serial.write(value & 0xFF);
    Serial.write((value >> 8) & 0xFF);
    Serial.write((value >> 16) & 0xFF);
    Serial.write((value >> 24) & 0xFF);
}

void sendInfo()
{
    sendUInt16(0xB416);           // 0
    sendUInt16(VERSION);          // 16
    sendUInt32(millis());         // 32
    sendUInt16(getFreeRam());     // 48
    sendUInt16(TOTAL_RAM);        // 64
    sendUInt32(FLASH_SIZE);       // 96
    sendUInt32(CPU_FREQ);         // 128
    Serial.write(BUFFER_SIZE);    // 160
    Serial.write(DIGITAL_PINS);   // 161
    Serial.write(TOTAL_PINS);     // 162
    Serial.write(MAX_SOFT_PWM);   // 163
    Serial.write(SOFT_PWM_FREQ);  // 164
    Serial.write(COMMANDS_COUNT); // 165
    Serial.write(SUCCESS_CODE);   // 166
    Serial.write(ERROR_CODE);     // 167

    static byte hwPins[] = {HARDWARE_PWM_PINS};
    Serial.write((byte)sizeof(hwPins));   // 168
    Serial.write(hwPins, sizeof(hwPins)); // 169

    Serial.write((byte)sizeof(INFO)); // 169 + hwPins.length
    Serial.write(INFO, sizeof(INFO)); // 170 + hwPins.length
}
