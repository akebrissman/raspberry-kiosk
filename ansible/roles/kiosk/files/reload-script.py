#!/usr/bin/python3
import os
import sys
import getopt
import json
import time
import requests
import socket
import subprocess
from datetime import datetime
# import cec


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


def chromium_load_url(url: str):
    browser = "chromium-browser"
    try:
        subprocess.check_output("chromium-browser --version", shell=True)
    except subprocess.CalledProcessError:
        browser = "chromium"

    # os.system(f"DISPLAY=:0 chromium-browser --same-tab '{result['url']}'") # Does not work
    os.system(f"DISPLAY=:0 {browser} '{url}'")


def chromium_refresh():
    os.system("DISPLAY=:0 xdotool key F5")


def chromium_kill_tabs():
    # os.system("DISPLAY=:0 xdotool key CTRL+F4") # Closes chromium if it is the last tab
    os.system('pkill -f -- "--type=renderer"')


def turn_on_off_tv():
    now = datetime.now().time()
    if now.hour == 8:
        print("Turn on TV")
        os.system("echo 'on 0' | cec-client -s -d 1")  # Turn on TV
        # cec.init()
        # tv = cec.Device(cec.CECDEVICE_TV)
        # tv.on()
    elif now.hour == 19:
        print("Turn off TV")
        os.system("echo 'standby 0' | cec-client -s -d 1")  # Turn off TV
        # cec.init()
        # tv = cec.Device(cec.CECDEVICE_TV)
        # tv.standby()


def get_meta_data() -> dict:
    # Extract meta data for cpu, memory and os
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

        with open('/sys/class/graphics/fb0/virtual_size', 'r') as f:
            meta["screen_res"] = f.read().strip()

    except FileNotFoundError:
        pass

    if "Serial" not in meta:
        try:
            output = subprocess.check_output("sudo dmidecode -t system", shell=True).decode("utf-8")
            for line in output.splitlines():
                if line.find("Serial Number") != -1:
                    meta["serial"] = line.split(":")[1].strip()
                if line.find("Product Name") != -1:
                    meta["model"] = line.split(":")[1].strip()
        except subprocess.CalledProcessError:
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
            if serial_in_file != serial:
                body = body.replace(serial_in_file, serial)
                f.seek(0)
                f.write(body)
    except FileNotFoundError:
        print("show-id.html not found")


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
    print("")
    print("Time", datetime.now())
    print("Model  : ", meta.get("model"))
    print("Serial : ", meta.get("serial"))
    print("OS name: ", meta.get("osPrettyName"))
    print("OS ver : ", meta.get("osVersion"))
    print("Total mem: ", meta.get("memTotal"))
    print("Free mem : ", meta.get("memFree"))
    print("Local IP: ", meta.get("local_ip"))
    print("Screen: ", meta.get("screen_res"))

    data = read_from_file()
    last_url = data.get('last-url')
    token = data.get('token')
    now = datetime.now().time()

    if not token or now.hour == 1:
        # Get a token once a day at 1 and make sure it does not expire for 24 hours
        token = sign_in()
        if token == "ERROR":
            data['token'] = None
            save_to_file(data)
            return
        else:
            data['token'] = token
            save_to_file(data)

    url = groupEndpoint + get_my_group_name(token, serial, local_ip)
    headers = {"Authorization": f"Bearer {token}", "X-Forwarded-For": local_ip}

    try:
        response = requests.get(url, headers=headers)
        if response.ok:
            result = response.json()
            print("URL: ", result['url'])

            if result['url'] != last_url:
                chromium_kill_tabs()
                chromium_load_url(result['url'])
                data ['last-url'] = result['url']
                save_to_file(data)
            else:
                # Reload current tab
                print("Refresh page")
                chromium_refresh()
        else:
            print(url)
            print(response.status_code, " ", response.text)
            chromium_load_url('show-id.html')
            save_to_file({'last-url': 'show-id.html'})

    except requests.exceptions.ConnectionError as e:
        print(e)
        chromium_load_url('show-id.html')
        save_to_file({'last-url': 'show-id.html'})

    turn_on_off_tv()


if __name__ == '__main__':
    start(sys.argv[1:])
