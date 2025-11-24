#!/usr/bin/env python3
# repl_client.py
# Arduino REPL client with:
#  - binary protocol support
#  - per-command arg & response parsers
#  - auto-port detection (no args)
#  - interactive REPL mode (infinite loop until Ctrl+C)
#  - autocompletion, aliases, history, run-from-file, repeat

import serial
import serial.tools.list_ports
import struct
import time
import argparse
import os
import json
from typing import List, Dict, Any, Tuple, Optional

# Try to import readline for autocompletion/history.
try:
    import readline
except Exception:
    try:
        import pyreadline3 as readline
    except Exception:
        readline = None

# ---------------------------
# Protocol constants
# ---------------------------

CMD_NOP = 0
CMD_INFO = 1
CMD_DIGITALREAD = 2
CMD_DIGITALWRITE = 3
CMD_ANALOGREAD = 4
CMD_ANALOGWRITE = 5
CMD_PINMODE = 6
CMD_RESET = 7

SUCCESS_CODE = 0xFF
ERROR_CODE = 0xFE

DEFAULT_BAUD = 9600

# ---------------------------
# Storage paths
# ---------------------------

HOME = os.path.expanduser("~")
HISTORY_FILE = os.path.join(HOME, ".repl_client_history")
ALIASES_FILE = os.path.join(HOME, ".repl_client_aliases.json")

# ---------------------------
# Alias handling
# ---------------------------

def alias_on(ser: serial.Serial, args: List[str]) -> Dict[str, Any]:
    if not args:
        return {"ok": False, "error": "on <pin>"}
    return run_one(ser, "digitalwrite", [args[0], "1"])

def alias_off(ser: serial.Serial, args: List[str]) -> Dict[str, Any]:
    if not args:
        return {"ok": False, "error": "off <pin>"}
    return run_one(ser, "digitalwrite", [args[0], "0"])

# ---------------------------
# Aliases
# ---------------------------

BUILTIN_ALIASES = {
    "i":   ("info", None),
    "dr":  ("digitalread", None),
    "ar":  ("analogread", None),
    "dw":  ("digitalwrite", None),
    "aw":  ("analogwrite", None),
    "pm":  ("pinmode", None),
    "r":   ("reset", None),
    "on":  ("digitalwrite", alias_on),
    "off": ("digitalwrite", alias_off),
}

REPL_COMMANDS_ALIASES = {
    "x": "exit",
    "quit": "exit",
    "q": "exit",
    "h": "help",
}

# ---------------------------
# Command handling
# ---------------------------

def build_args_nop(args: List[str]) -> bytes: return b''
def build_args_digitalread(args: List[str]) -> bytes:
    if len(args) < 1: raise ValueError("digitalread requires pin number")
    return bytes([int(args[0])])
def build_args_analogread(args: List[str]) -> bytes:
    if len(args) < 1: raise ValueError("analogread requires pin number")
    return bytes([int(args[0])])
def build_args_digitalwrite(args: List[str]) -> bytes:
    if len(args) < 2: raise ValueError("digitalwrite requires pin and value")
    val = args[1]
    if isinstance(val, str):
        if val.lower() in ("on", "true", "high", "h"): 
            val = 1
        elif val.lower() in ("off", "false", "low", "l"): 
            val = 0
    return bytes([int(args[0]), int(val) & 0xFF])
def build_args_analogwrite(args: List[str]) -> bytes:
    if len(args) < 2: raise ValueError("analogwrite requires pin and value")
    return bytes([int(args[0]), int(args[1]) & 0xFF])
def build_args_pinmode(args: List[str]) -> bytes:
    if len(args) < 2: raise ValueError("pinmode requires pin and mode")
    mode = args[1]
    if isinstance(mode, str):
        if mode.lower() in ("in", "input"): 
            mode = 0
        elif mode.lower() in ("out", "output"): 
            mode = 1
        elif mode.lower() in ("input_pullup", "pullup"): 
            mode = 2
    return bytes([int(args[0]), int(mode) & 0xFF])

def parse_response_without_payload(payload: bytes, term: int) -> Dict[str, Any]: return {"ok": term == SUCCESS_CODE}
def parse_response_reset(payload: bytes, term: int) -> Dict[str, Any]:
    return {"ok": term == SUCCESS_CODE, "note": "device reset likely triggered"}
def parse_response_digitalread(payload: bytes, term: int) -> Dict[str, Any]:
    if term == ERROR_CODE: return {"ok": False, "error": "device error"}
    if len(payload) < 1:
        return {"ok": False, "error": "short payload"}
    return {"ok": True, "value": payload[0]}
def parse_response_analogread(payload: bytes, term: int) -> Dict[str, Any]:
    if term == ERROR_CODE: return {"ok": False, "error": "device error"}
    if len(payload) < 2:
        return {"ok": False, "error": "short payload"}
    val, = struct.unpack_from("<H", payload)
    return {"ok": True, "value": val}
def parse_response_info(payload: bytes, term: int) -> Dict[str, Any]:
    try:
        off = 0
        millis, = struct.unpack_from("<I", payload, off); off += 4
        free_ram, = struct.unpack_from("<H", payload, off); off += 2
        total_ram, = struct.unpack_from("<H", payload, off); off += 2
        flash_size, = struct.unpack_from("<I", payload, off); off += 4
        cpu_freq, = struct.unpack_from("<I", payload, off); off += 4
        version, = struct.unpack_from("<I", payload, off); off += 4

        buffer_size = payload[off]; off += 1
        digital_pins = payload[off]; off += 1
        total_pins = payload[off]; off += 1
        max_soft_pwm = payload[off]; off += 1
        soft_pwm_freq = payload[off]; off += 1
        commands_count = payload[off]; off += 1
        succ = payload[off]; off += 1
        err = payload[off]; off += 1

        hw_len = payload[off]; off += 1
        hw = list(payload[off:off+hw_len]); off += hw_len

        info_len = payload[off]; off += 1
        info_str = payload[off:off+info_len].decode("ascii", "replace")

        return {
            "ok": term == SUCCESS_CODE,
            "millis": millis,
            "free_ram": free_ram,
            "total_ram": total_ram,
            "flash_size": flash_size,
            "cpu_freq": cpu_freq,
            "version": version,
            "buffer_size": buffer_size,
            "digital_pins": digital_pins,
            "total_pins": total_pins,
            "max_soft_pwm": max_soft_pwm,
            "soft_pwm_freq": soft_pwm_freq,
            "commands_count": commands_count,
            "success_code": succ,
            "error_code": err,
            "hardware_pwm": hw,
            "info": info_str
        }
    except Exception as e:
        return {"ok": False, "error": f"parse fail: {e}"}

COMMANDS = {
    "nop":          (CMD_NOP,          build_args_nop,          parse_response_without_payload),
    "info":         (CMD_INFO,         build_args_nop,          parse_response_info           ),
    "digitalread":  (CMD_DIGITALREAD,  build_args_digitalread,  parse_response_digitalread    ),
    "digitalwrite": (CMD_DIGITALWRITE, build_args_digitalwrite, parse_response_without_payload),
    "analogread":   (CMD_ANALOGREAD,   build_args_analogread,   parse_response_analogread     ),
    "analogwrite":  (CMD_ANALOGWRITE,  build_args_analogwrite,  parse_response_without_payload),
    "pinmode":      (CMD_PINMODE,      build_args_pinmode,      parse_response_without_payload),
    "reset":        (CMD_RESET,        build_args_nop,          parse_response_reset          ),
}

# ---------------------------
# REPL command handling
# ---------------------------

def repl_help(state: Dict[str, Any], args: List[str]) -> None:
    show_help()

def repl_exit(state: Dict[str, Any], args: List[str]) -> None:
    save_history()
    print("Exit.")
    raise KeyboardInterrupt

def repl_aliases(state: Dict[str, Any], args: List[str]) -> None:
    show_aliases()

def repl_alias(state: Dict[str, Any], args: List[str]) -> None:
    if len(args) == 0:
        show_aliases()
        return
    sub = args[0]
    if sub == "add" and len(args) >= 3:
        alias_name = args[1]
        target = args[2]
        user_aliases[alias_name] = target
        save_user_aliases(user_aliases)
        print(f"alias added: {alias_name} -> {target}")
    elif sub == "rm" and len(args) >= 2:
        alias_name = args[1]
        if alias_name in user_aliases:
            user_aliases.pop(alias_name)
            save_user_aliases(user_aliases)
            print(f"alias removed: {alias_name}")
        else:
            print("alias not found")
    else:
        print("usage: alias add <alias> <command> | alias rm <alias>")

def repl_history(state: Dict[str, Any], args: List[str]) -> None:
    if not readline:
        print("history not available on this platform")
    else:
        for i in range(1, readline.get_current_history_length() + 1):
            print(i, readline.get_history_item(i))

def repl_json(state: Dict[str, Any], args: List[str]) -> None:
    if len(args) >= 1:
        val = args[0].lower()
        if val in ("on", "true", "1"):
            state["json"] = True
            print("json on")
        elif val in ("off", "false", "0"):
            state["json"] = False
            print("json off")
        else:
            print("usage: json on|off")
    else:
        print("json", "on" if state["json"] else "off")

def repl_run(state: Dict[str, Any], args: List[str]) -> None:
    if len(args) < 1:
        print("usage: run <file>")
        return
    fname = args[0]
    if not os.path.exists(fname):
        print("file not found:", fname)
        return
    try:
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                print("> " + line)
                subparts = line.split()
                subcmd = subparts[0].lower()
                subargs = subparts[1:]
                res = run_one(state["ser"], subcmd, subargs)
                print_res(res, state["json"])
    except Exception as e:
        print(f"error reading file: {e}")

def repl_repeat(state: Dict[str, Any], args: List[str]) -> None:
    if len(args) < 2:
        print("usage: repeat <count> <command...>")
        return
    try:
        count = int(args[0])
    except ValueError:
        print("count must be integer")
        return
    subparts = args[1:]
    for _ in range(count):
        res = run_one(state["ser"], subparts[0], subparts[1:])
        print_res(res, state["json"])
        time.sleep(0.1)

def repl_rvd(state: Dict[str, Any], args: List[str]) -> None:
    if len(args) < 2:
        print("usage: rvd <count> <command...>")
        return
    try:
        count = int(args[0])
    except ValueError:
        print("count must be integer")
        return
    subparts = args[1:]
    for _ in range(count):
        res = run_one(state["ser"], subparts[0], subparts[1:])
        print(res.get("value", "N/A"))
        time.sleep(0.1)

REPL_COMMANDS = {
    "help":    repl_help,
    "quit":    repl_exit,
    "aliases": repl_aliases,
    "alias":   repl_alias,
    "history": repl_history,
    "json":    repl_json,
    "run":     repl_run,
    "repeat":  repl_repeat,
    "rvd":     repl_rvd,
}

# ---------------------------
# Aliases loading/saving
# ---------------------------

def load_user_aliases() -> Dict[str, str]:
    try:
        if os.path.exists(ALIASES_FILE):
            with open(ALIASES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}

def save_user_aliases(aliases: Dict[str, str]) -> None:
    try:
        with open(ALIASES_FILE, "w", encoding="utf-8") as f:
            json.dump(aliases, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

user_aliases = load_user_aliases()

def resolve_alias(cmd: str) -> str:
    if cmd in user_aliases:
        return user_aliases[cmd]
    if cmd in BUILTIN_ALIASES:
        return BUILTIN_ALIASES[cmd][0]
    return cmd

# ---------------------------
# Port utilities & IO helpers
# ---------------------------

def list_serial_ports() -> List[str]:
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

def auto_detect_port() -> Optional[str]:
    ports = list_serial_ports()
    priority = [p for p in ports if ("ACM" in p or "USB" in p or "COM" in p)]
    if priority:
        return priority[0]
    return ports[0] if ports else None

def open_port(port: str, baud: int = DEFAULT_BAUD, timeout: float = 0.1) -> serial.Serial:
    s = serial.Serial(port, baudrate=baud, timeout=timeout)
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(2)  # Wait for Arduino to reset
    return s

def send_command(ser: serial.Serial, cmd: int, args: bytes = b'') -> None:
    ser.write(bytes([cmd]) + args)
    ser.flush()

def read_response(ser: serial.Serial, overall_timeout: float = 2.0, quiet_time: float = 0.02) -> Optional[bytes]:
    buf = bytearray()
    start = time.monotonic()
    original_timeout = ser.timeout
    ser.timeout = quiet_time
    try:
        while (time.monotonic() - start) < overall_timeout:
            b = ser.read(1)
            if not b:
                if buf and buf[-1] in (SUCCESS_CODE, ERROR_CODE):
                    return bytes(buf)
                continue
            buf.append(b[0])
            if buf[-1] in (SUCCESS_CODE, ERROR_CODE):
                tail = ser.read(1)
                if not tail:
                    return bytes(buf)
                buf.append(tail[0])
        return bytes(buf) if buf else None
    finally:
        ser.timeout = original_timeout

def split_payload_and_terminator(resp: bytes) -> Tuple[bytes, int]:
    if not resp:
        return b'', -1
    return resp[:-1], resp[-1]

# ---------------------------
# High-level executor
# ---------------------------

def print_res(res: Dict[str, Any], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for k, v in res.items():
            print(f"{k}: {v}")

def run_one(ser: serial.Serial, name: str, a: List[str]) -> Dict[str, Any]:
    name_real = resolve_alias(name)

    if name in BUILTIN_ALIASES:
        handler = BUILTIN_ALIASES[name][1]
        if handler is not None:
            return handler(ser, a)

    if name_real not in COMMANDS:
        return {"ok": False, "error": f"unknown command: {name_real}"}

    code, build, parse = COMMANDS[name_real]
    try:
        args = build(a)
    except Exception as e:
        return {"ok": False, "error": f"arg build error: {e}"}

    send_command(ser, code, args)
    raw = read_response(ser)
    if raw is None:
        return {"ok": False, "error": "no response"}

    payload, term = split_payload_and_terminator(raw)
    return parse(payload, term)

# ---------------------------
# Autocomplete + history
# ---------------------------

def setup_readline() -> None:
    if not readline:
        return
    try:
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
    except Exception:
        pass

    completions = sorted(set(
        list(COMMANDS.keys()) + 
        list(BUILTIN_ALIASES.keys()) + 
        list(user_aliases.keys()) + 
        list(REPL_COMMANDS.keys())
    ))

    def completer(text: str, state: int) -> Optional[str]:
        buffer = readline.get_line_buffer()
        tokens = buffer.split()
        if len(tokens) <= 1:
            opts = [c for c in completions if c.startswith(text)]
        else:
            opts = []
        try:
            return opts[state]
        except IndexError:
            return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

def save_history() -> None:
    if not readline:
        return
    try:
        readline.write_history_file(HISTORY_FILE)
    except Exception:
        pass

# ---------------------------
# REPL utilities
# ---------------------------

def show_help() -> None:
    print("REPL local commands:")
    print("  help, h             - show this message")
    print("  exit, quit, q       - exit client")
    print("  aliases             - list aliases")
    print("  alias add <a> <cmd> - add alias (persists)")
    print("  alias rm <a>        - remove alias")
    print("  run <file>          - execute commands from file (one per line)")
    print("  repeat N <cmd...>   - repeat N times (0.1s pause)")
    print("  rvd N <cmd...>      - repeat N times (0.1s pause), but display only 'value' field")
    print("  json on|off         - toggle JSON-style responses display")
    print("")
    print("Arduino commands (you can use aliases):")
    for name in sorted(COMMANDS.keys()):
        print(" ", name)
    print("")

def show_aliases() -> None:
    print("builtin aliases:")
    for a, t in BUILTIN_ALIASES.items():
        print(f"  {a} -> {t[0]}")
    if user_aliases:
        print("user aliases:")
        for a, t in user_aliases.items():
            print(f"  {a} -> {t}")

# ---------------------------
# REPL
# ---------------------------

def interactive_repl(ser: serial.Serial, json_mode: bool) -> None:
    state = {"ser": ser, "json": json_mode}

    if readline:
        setup_readline()

    print("Interactive Arduino REPL. Ctrl+C to exit. 'help' for commands.")

    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in REPL_COMMANDS_ALIASES:
                cmd = REPL_COMMANDS_ALIASES[cmd]
            if cmd in REPL_COMMANDS:
                REPL_COMMANDS[cmd](state, args)
                continue

            res = run_one(ser, cmd, args)
            print_res(res, state["json"])
    except KeyboardInterrupt:
        print("\nExit.")
        save_history()

# ---------------------------
# CLI handling
# ---------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Arduino REPL client")
    parser.add_argument("--port", "-p", help="serial port")
    parser.add_argument("--baud", "-b", type=int, default=DEFAULT_BAUD, help="baud rate")
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("command", nargs="?", help="command name")
    parser.add_argument("args", nargs="*", help="command arguments")
    arg = parser.parse_args()

    port = arg.port or auto_detect_port()
    if not port:
        print("No serial ports available.")
        return
    ser = open_port(port, arg.baud)

    try:
        if arg.command is None:  # REPL mode
            interactive_repl(ser, arg.json)
        else:  # One-shot mode
            res = run_one(ser, arg.command, arg.args)
            print_res(res, arg.json)
    finally:
        try:
            ser.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
