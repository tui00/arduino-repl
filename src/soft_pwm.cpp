#include "soft_pwm.h"
#include "config.h"
#include "utils.h"

SoftPWM softPWM[MAX_SOFT_PWM];
byte softPWMCount = 0;

bool setPWM(byte pin, byte dutyCycle)
{
    if (isHardwarePWMPin(pin))
    {
        analogWrite(pin, dutyCycle);
        return true;
    }

    digitalWrite(pin, LOW);

    byte index = 0;
    for (; index < softPWMCount; index++)
    {
        if (softPWM[index].pin == pin || !softPWM[index].enabled)
            break;
    }
    if (index >= MAX_SOFT_PWM)
        return false;

    if (dutyCycle == 0)
    {
        if (index < softPWMCount)
            softPWM[index].enabled = false;
        return true;
    }

    if (index == softPWMCount)
        softPWMCount++;

    softPWM[index] = {pin, dutyCycle, millis(), false, true};
    return true;
}

void resetPWM(byte pin)
{
    byte i = 0;
    for (; i < softPWMCount; i++)
    {
        if (softPWM[i].pin == pin)
        {
            softPWM[i].enabled = false;
            break;
        }
    }
}

void updateSoftPWM()
{
    unsigned long now = millis();
    for (byte i = 0; i < softPWMCount; i++)
    {
        if (!softPWM[i].enabled)
            continue;

        unsigned long period = 1000 / SOFT_PWM_FREQ;
        unsigned long onTime = (period * softPWM[i].dutyCycle) / 255;
        unsigned long elapsed = now - softPWM[i].lastToggle;

        if (softPWM[i].state && elapsed >= onTime)
        {
            digitalWrite(softPWM[i].pin, LOW);
            softPWM[i].state = false;
            // softPWM[i].lastToggle = now; // Так работает лучше
        }
        else if (!softPWM[i].state && elapsed >= period)
        {
            digitalWrite(softPWM[i].pin, HIGH);
            softPWM[i].state = true;
            softPWM[i].lastToggle = now;
        }
    }
}
