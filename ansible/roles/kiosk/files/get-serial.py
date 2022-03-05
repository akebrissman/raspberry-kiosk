#!/usr/bin/python3

def get_serial() -> str:
    # Extract serial from cpuinfo file
    cpu_serial: str = "0000000000000000"
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    cpu_serial = line[10:26]
    except FileNotFoundError:
        cpu_serial = "ERROR000000000"

    return cpu_serial

print(get_serial())
