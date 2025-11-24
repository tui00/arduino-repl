#pragma once
#include <Arduino.h>
#include "soft_pwm.h"

enum Command {
    CMD_NOP          = 0,
    CMD_INFO         = 1,
    CMD_DIGITALREAD  = 2,
    CMD_DIGITALWRITE = 3,
    CMD_ANALOGREAD   = 4,
    CMD_ANALOGWRITE  = 5,
    CMD_PINMODE      = 6,
    CMD_RESET        = 7,
};

struct CommandResult {
    bool hasError;
    bool hasOutput;
    bool isTwoByteOutput;
    uint16_t outputValue;
};

int getRequiredArgs(byte command);
bool hasCompleteCommand();
void executeBufferedCommand();
void sendResponse();
