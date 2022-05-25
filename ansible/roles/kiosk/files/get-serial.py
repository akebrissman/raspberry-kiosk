#!/usr/bin/python3
import subprocess


def get_serial() -> str:
    cpu_serial: str = "00000"
    try:
        # Extract serial from cpuinfo file
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    cpu_serial = line[10:26]
    except FileNotFoundError:
        pass

    if cpu_serial == "00000":
        try:
            # Extract serial from dmidecode
            output = subprocess.check_output("sudo dmidecode -t system", shell=True).decode("utf-8")
            for line in output.splitlines():
                if line.find("Serial Number") != -1:
                    cpu_serial = line.split(":")[1].strip()
                    break
        except subprocess.CalledProcessError:
            pass

    return cpu_serial


print(get_serial())
