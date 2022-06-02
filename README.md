# raspberry-kiosk
This project set up a Raspberry Pi in kiosk mode using an Ansible Playbook


Getting started
===============

Prepare installation
--------------------
```bash 
Clone the project
cd raspberry-kiosk
# On Windows, switch to the project folder from "Windows Sub System For Linux" (Ubunutu)
# cd /mnt/c/.../.../raspberry-kiosk
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
```

Setup options and configuration
-------------------------------
- Update the inventory.ini or modify one of the sample files
  - Add the server(s) to the **[pi_kiosk]** section

    **host_name** sets the host name <br/>
    **host_type** tells if the target device runs Raspberry Pi OS desktop or lite 


  - Select any of the three setup options
    - Static page

      Assign a URL to the **kiosk_url** variable, in the **[pi_kiosk:vars]** section, when you want to launch the URL in the browser <br/>
      See sample file: **inventory.ini**
      ```bash
      [pi_kiosk:vars]
      kiosk_url=https://lite.cnn.com/en
      ansible_python_interpreter=/usr/bin/python3
      ```
    - Auto-reload page

      Assign a URL to the **kiosk_iframe_url** variable, in the **[pi_kiosk:vars]** section, when you want to launch the URL in an iframe (refreshed by javascript every hour) <br/>
      See sample file: **inventory-iframe.ini**
      ```bash
      [pi_kiosk:vars]
      kiosk_iframe_url=https://lite.cnn.com/en
      ansible_python_interpreter=/usr/bin/python3
      ```
    - Script based reload of page

      Set the file name 'show-id.html' to the **kiosk_url** parameter in the **[pi_kiosk:vars]** section, when you want to show the device id on the screen after installation. 
      The device id is used to differentiate the content per player when using a  backend service like https://github.com/akebrissman/gateway. With a backend service you can group devices and then let a script check for what URL to show for each device.

      The **cron_check_minute** sets the interval for the reload-script to be called and the page to be refreshed.<br/>
      The **lookup_server** is the URL to the backend server to get the URL.<br/>
      The **auth_** parameters are used for signing in and receiving a Bearer Token used in the backend API requests.<br/>
      See sample file: **inventory-iframe.ini** 
      ```bash
      [pi_kiosk:vars]
      kiosk_url=/home/pi/show-id.html
      cron_check_minute="0****"
      lookup_server=https://viewspot.server.se
      auth_domain=https://user.eu.auth0.com/oauth/token
      auth_client_id=tur755ygFUryfSKm8DR9W
      auth_client_secret=UShRsA6y9hV_Dy7Fl
      auth_audience=my-project-api
      auth_grant_type=client_credentials
      ansible_python_interpreter=/usr/bin/python3
      ```

Run the playbook
----------------
```bash
cd ansible
# First time you need to be prompted for the password  since the keys are not applied yet
ansible-playbook playbook.yml -i inventory.ini --user <user> --ask-pass --diff -vv

# Thereafter you can skip the --ask-pass if your put your public key in the public_keys folder
ansible-playbook playbook.yml -i inventory.ini --diff -vv
# To only update the kiosk settings
ansible-playbook playbook.yml -i inventory.ini --tags kiosk --diff -vv

```

Project information
-------------------
- The application is run as the default user created during the image creation and used for deployment 
- The public_keys are stored in the 'ansible/public_keys' folder
- The keys are assigned to the default user in playbook.yml
- The Authentication is using Client Credentials Grant Type

