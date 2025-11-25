# Arduino REPL
[![License](https://img.shields.io/github/license/tui00/arduino-repl)](https://github.com/tui00/arduino-repl/blob/main/LICENSE)
[![Last release version](https://img.shields.io/github/v/release/tui00/arduino-repl?include_prereleases)](https://github.com/tui00/arduino-repl/releases)
[![Static Badge](https://img.shields.io/badge/English-README-red)](https://github-com.translate.goog/tui00/arduino-repl/blob/main/README.md?_x_tr_sl=ru&_x_tr_tl=en&_x_tr_hl=ru&_x_tr_pto=wapp)

## Краткое описание
Это REPL для Arduino.

## Этот проект уже готов
Он был написан за один день для другого моего проекта. README был скопирован из проекта [LLAC](https://github.com/tui00/LLAC/) с небольшими изменениями.

## Скачивание проекта
> **⚠️ Этими способами вы можете скачать только `Debug` версию. Если нужна `Release` версия, перейдите во вкладку [`Releases`](https://github.com/tui00/arduino-repl/releases)**
- С помощью ссылки:
  - Откройте [ссылку](https://github.com/tui00/arduino-repl/archive/refs/heads/main.zip)
- С помощью Github CLI:  
  - Запустите `gh repo clone tui00/arduino-repl`
- С помощью git:  
  - Запустите `git clone https://github.com/tui00/arduino-repl.git`
- С помощью рук:
  - Откройте раздел `Code`
  - Нажмите `Download ZIP`

## Запуск проекта
> **⚠️ Для запуска установите `.NET 9.0 Runtime`**
- Запустите команду `dotnet build`
- Откройте папку `bin/Debug/net9.0`
- Запустите исполняемый файл

## Краткая документация
### Формат
Каждая команда имеет формат:
```
<Код команды>\[<Аргументы> ...\]
```
Ответ от Arduino:
```
\[<Ответы> ...\]<SUCCESS_CODE>
```
При ошибке:
```
<ERROR_CODE>
```
### Файл `src/config.h`
#### Конфигурация REPL
`VERSION` -- Версия REPL (необязательно)  
`INFO` -- Строка с информация о прошивке (необязательно)  
`BAUDRATE` -- Скорость обмена данными  
`COMMANDS_COUNT` -- количество команд  
`SUCCESS_CODE` -- Код успеха  
`ERROR_CODE` -- Код ошибки  
`BUFFER_SIZE` -- Размер буфера для команд  
`MAX_SOFT_PWM` -- Максимальное количество программируемых ШИМ пинов   
`SOFT_PWM_FREQ` -- Частота ШИМ  
#### Информация о микроконтроллере
`TOTAL_RAM` -- Общий размер RAM на микроконтроллере (необязательно)  
`FLASH_SIZE` -- Размер Flash памяти на микроконтроллере (необязательно)  
`CPU_FREQ` -- Частота процессора микроконтроллера (необязательно)  
`HARDWARE_PWM_PINS` -- Пины с аппаратным ШИМ  
`DIGITAL_PINS` -- Количество цифровых пинов  
`TOTAL_PINS` -- Всего пинов на микроконтроллере  
### Ответ команды `info`
```
0xB416(16 бит)
версия repl(16 бит)
millis(32 бит)
свободная ram(в байтах)(16 бит)
всего ram(в байтах)(16 бит)
размер flash(в байтах)(32 бит)
частота cpu(в герцах)(32 бит)
размер буфера(8 бит)
кол-во digital пинов(8 бит)
всего пинов(8 бит)
максимальное кол-во soft-pwm(8 бит)
кол-во команд(8 бит)
код успеха(8 бит)
код ошибки(8 бит)
кол-во пинов с hard-pwm(8 бит)
пины с hard-pwm(8 бит каждый)
кол-во символов INFO(8 бит)
INFO(8 бит каждый)
```
### Коды комманд
#### Arduino
`digiralRead` -- 0x2,  
`digiralWrite` -- 0x3,  
`analogRead` -- 0x4,  
`analogWrite` -- 0x5,  
`pinMode` -- 0x6,  
### REPL
`nop` -- 0x0,  
`info` -- 0x1,  
`reset` -- 0x7,  
### Добавление своей команды
* В `src/commands.h` добавте в `enum Command` команду и её код.
* В `src/commands.cpp` в функции `getRequiredArgs` добавте кол-во аргументов для вашей команды
* В `src/commands.cpp` в функции `executeBufferedCommand` добавте реализацию для вашей команды

## Конец
На этом все
