#!/usr/bin/python3
import os
import sys
import getopt
import json
import time
import requests
import socket
from datetime import datetime


auth_domain = os.getenv("KIOSK_AUTH_DOMAIN", "your domain.com")
auth_data = {"client_id": os.getenv("KIOSK_AUTH_CLIENT_ID", "your client id"),
             "client_secret": os.getenv("KIOSK_AUTH_CLIENT_SECRET", "your client secret"),
             "audience": os.getenv("KIOSK_AUTH_API_AUDIENCE", "your audience"),
             "grant_type": os.getenv("KIOSK_AUTH_GRANT_TYPE", "your grant type")
             }
server = os.getenv("KIOSK_SERVER", "your.audience.com")
groupEndpoint = server + '/api/group/'
deviceEndpoint = server + '/api/device/'


def save_to_file(data: dict):
    try:
        json_obj = json.dumps(data)
        with open("/run/shm/kiosk-config.json", "w") as f:
            f.write(json_obj)
    except Exception as e:
        print(e)


def read_from_file() -> dict:
    try:
        with open("/run/shm/kiosk-config.json", "r") as f:
            json_str = f.read()
            data = json.loads(json_str)
    except FileNotFoundError:
        data = {'last-url': ''}
    return data


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except socket.error:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip


def get_meta_data() -> dict:
    # Extract meta data for cpu, memory, os file
    meta = {}
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                data = line.split(":")
                if data[0].strip() == "Serial":
                    meta["serial"] = data[1].strip()
                if data[0].strip() == "Model":
                    meta["model"] = data[1].strip()

        with open('/etc/os-release', 'r') as f:
            for line in f:
                data = line.split("=")
                if data[0].strip() == "PRETTY_NAME":
                    meta["osPrettyName"] = data[1].rstrip("\n").strip('"')
                if data[0].strip() == "VERSION":
                    meta["osVersion"] = data[1].rstrip("\n").strip('"')

        with open('/proc/meminfo', 'r') as f:
            for line in f:
                data = line.split(":")
                if data[0].strip() == "MemTotal":
                    meta["memTotal"] = data[1].strip()
                if data[0].strip() == "MemFree":
                    meta["memFree"] = data[1].strip()

    except FileNotFoundError:
        pass

    meta["local_ip"] = get_local_ip()

    return meta


def update_show_id_file(serial: str):
    try:
        with open("show-id.html", "r+") as f:
            body = f.read()
            start_pos = body.find("<p>")
            if start_pos > 0:
                start_pos = start_pos + 3
            end_pos = body.find("</p>")
            serial_in_file = body[start_pos:end_pos]
            if serial != serial:
                body = body.replace(serial_in_file, serial)
                f.seek(0)
                f.write(body)
    except FileNotFoundError:
        print("No show-id.html file")


def sign_in() -> str:
    access_token: str = "ERROR"
    headers = {"content-type": 'application/json'}
    try:
        response = requests.post(auth_domain, headers=headers, data=json.dumps(auth_data))
        if response.ok:
            result = response.json()
            access_token = result["access_token"]
        else:
            print(response.status_code, " ", response.text)

    except requests.exceptions.ConnectionError as e:
        print(e)

    return access_token


def get_my_group_name(token: str, serial: str, local_ip: str) -> str:
    url: str = deviceEndpoint + serial
    group_name: str = "ERROR"
    headers = {"Authorization": f"Bearer {token}", "X-Forwarded-For": local_ip}
    retry_count = 5

    while retry_count > 0:
        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                result = response.json()
                group_name = result['group']
            else:
                print(response.status_code, " ", response.text)
            break
        except requests.exceptions.ConnectionError as e:
            time.sleep(retry_count)
            retry_count -= 1
            print(f"Remaining attempts: {retry_count}")
            print(url)
            print(e)

    return group_name


def start(argv):
    try:
        opts, args = getopt.getopt(argv, "t:", ["time="])
    except getopt.GetoptError:
        print('Invalid arguments')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-t", "--time"):
            print(arg)
            time.sleep(int(arg))

    meta = get_meta_data()
    serial = meta.get("serial")
    local_ip = meta.get("local_ip")
    update_show_id_file(serial)
    print("Time", datetime.now())
    print("Model  : ", meta.get("model"))
    print("Serial : ", meta.get("serial"))
    print("OS name: ", meta.get("osPrettyName"))
    print("OS ver : ", meta.get("osVersion"))
    print("Total mem: ", meta.get("memTotal"))
    print("Free mem : ", meta.get("memFree"))
    print("Local IP: ", meta.get("local_ip"))

    token = sign_in()
    if token == "ERROR":
        return

    url = groupEndpoint + get_my_group_name(token, serial, local_ip)
    headers = {"Authorization": f"Bearer {token}", "X-Forwarded-For": local_ip}

    try:
        response = requests.get(url, headers=headers)
        if response.ok:
            result = response.json()
            print("URL to load", result['url'])

            last_url = read_from_file()['last-url']
            if result['url'] != last_url:
                # Delete current Tab
                # os.system("DISPLAY=:0 xdotool key CTRL+F4") # Closes chromium if it is the last tab
                os.system('pkill -f -- "--type=renderer"')

                # Load new url
                # os.system(f"DISPLAY=:0 chromium-browser --same-tab '{result['url']}'") # Does not work
                os.system(f"DISPLAY=:0 chromium-browser '{result['url']}'")

                save_to_file({'last-url': result['url']})
            else:
                # Reload current tab
                print("Refresh")
                os.system("DISPLAY=:0 xdotool key F5")
        else:
            print(url)
            print(response.status_code, " ", response.text)
            os.system(f"DISPLAY=:0 chromium-browser 'show-id.html'")
            save_to_file({'last-url': 'show-id.html'})

    except requests.exceptions.ConnectionError as e:
        print(e)
        os.system(f"DISPLAY=:0 chromium-browser 'show-id.html'")
        save_to_file({'last-url': 'show-id.html'})


if __name__ == '__main__':
    start(sys.argv[1:])
