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
- Add the server(s) to the inventory.ini
- Update the roles/kiosk/files/index.html file and add what file you want to be loaded in the iframe
- Update the "Update autostart file" section in the roles/kiosk/tasks/main.yml and add the file you want to load (if you don't use iframe)

Run the playbook
----------------
```bash
cd ansible
ansible-playbook playbook.yml -i inventory.ini -vv
# First  time it must be the command below since the keys are not applied yet
ansible-playbook playbook.yml -i inventory.ini --ask-become-pass -vv
# To only update the kiosk settings
ansible-playbook playbook.yml -i inventory.ini --tags kiosk -vv
```

Project information
-----------
- The user is the default user 'pi'
- The public_keys are stored in the 'ansible/public_keys' folder. 
- The keys are assigned to the user 'pi' in playbook.yml which must be updated if new keys are added. 

