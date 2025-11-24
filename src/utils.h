#pragma once
#include <Arduino.h>

int getFreeRam();
byte readPin(byte pin, bool& error);
bool isHardwarePWMPin(byte pin);
