# raspberry-kiosk
This project set up a Raspberry Pi in kiosk mode


Getting started
===============

Prepare installation
--------------------
```bash 
Clone the project
cd raspberry-kiosk
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
```

Update configuration
--------------------
- Update the inventory.ini
  - Add the server(s) to the **[pi_kiosk]** section
  
  - Select any of the three options
    - Static page
      
      Assign a URL to the **kiosk_url** variable, in the **[pi_kiosk:vars]** section, if you want to launch the url direct in the browser
      ```bash
      [pi_kiosk:vars]
      kiosk_url=https://google.com
      ansible_python_interpreter=/usr/bin/python3
      ```
    - Auto-reload page
      
      Assign a URL to the **kiosk_iframe_url** variable, in the **[pi_kiosk:vars]** section, if you want to launch the url in an iframe (refreshed by javascript every hour)
      ```bash
      [pi_kiosk:vars]
      kiosk_iframe_url="https:news-flash.com"
      ansible_python_interpreter=/usr/bin/python3
      ```
    - Script based reload of page
      
      Set 'show-id.html' as the **kiosk_url** in the **[pi_kiosk:vars]** section, to show the device id on the screen after installation. 
      The device id can be added to a backend service like https://github.com/akebrissman/gateway, where you can group devices and then let a script, run by cron, check for what url to show for each specific device. See reload-script.py
      
      Set the refresh time to the **cron_check_minute** to call the reload-script with an interval
       
      ```bash
      [pi_kiosk:vars]
      kiosk_url=/home/pi/show-id.html
      cron_check_minute="0****"
      ansible_python_interpreter=/usr/bin/python3
      ```

Run the playbook
----------------
```bash
cd ansible
ansible-playbook playbook.yml -i inventory.ini --diff -vv
# To only update the kiosk settings
ansible-playbook playbook.yml -i inventory.ini --tags kiosk --diff -vv
# First  time you need to be prompted for the password  since the keys are not applied yet
ansible-playbook playbook.yml -i inventory.ini --user pi --ask-pass --diff -vv

```

Project information
-----------
- The user is the default user 'pi'
- The public_keys are stored in the 'ansible/public_keys' folder. 
- The keys are assigned to the user 'pi' in playbook.yml which must be updated if new keys are added. 

