#include "utils.h"
#include "config.h"

int getFreeRam() {
    extern int __heap_start, *__brkval;
    int v;
    return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

byte readPin(byte pin, bool& error) {
    if (pin < DIGITAL_PINS) return pin;
    if (pin < TOTAL_PINS) return pin - DIGITAL_PINS + A0;

    error = true;
    return 0;
}

bool isHardwarePWMPin(byte pin) {
    byte hwPins[] = {HARDWARE_PWM_PINS};
    for (byte i = 0; i < sizeof(hwPins); i++) {
        if (hwPins[i] == pin) return true;
    }
    return false;
}
