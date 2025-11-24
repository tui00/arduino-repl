#pragma once
#include <Arduino.h>

struct SoftPWM {
    byte pin;
    byte dutyCycle;
    unsigned long lastToggle;
    bool state;
    bool enabled;
};

extern SoftPWM softPWM[];
extern byte softPWMCount;

bool setPWM(byte pin, byte dutyCycle);
void resetPWM(byte pin);
void updateSoftPWM();
