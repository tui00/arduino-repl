#pragma once

// Конфигурация REPL
#define VERSION 1 // Версия REPL
#define INFO "Arduino REPL v1.0" // Информация о прошивке
#define BAUDRATE 115200 // Скорость обмена данными
#define COMMANDS_COUNT 8 // Количество команд, доступных для REPL
#define SUCCESS_CODE 0xFF // Код успеха
#define ERROR_CODE 0xFE // Код ошибки
#define BUFFER_SIZE 10 // Размер буфера для команд
#define MAX_SOFT_PWM 6 // Максимальное количество программируемых ШИМ пинов
#define SOFT_PWM_FREQ 50 // Частота ШИМ

// Информация о микроконтроллере
#define TOTAL_RAM 2048 // Общий размер RAM на микроконтроллере
#define FLASH_SIZE 32256 // Размер Flash памяти на микроконтроллере
#define CPU_FREQ 16000000L // Частота процессора микроконтроллера
#define HARDWARE_PWM_PINS 3, 5, 6, 9, 10, 11 // Пины с аппаратным ШИМ
#define DIGITAL_PINS 14 // Количество цифровых пинов
#define TOTAL_PINS 22 // Всего пинов на микроконтроллере
