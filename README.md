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
  - Assign a URL to the **kiosk_url** variable if you want to launch the url direct in the browser
  - Assign a URL to the **kiosk_iframe_url** variable if you want to launch the url in an iframe (refreshed every hour)

Run the playbook
----------------
```bash
cd ansible
ansible-playbook playbook.yml -i inventory.ini --diff -vv
# To only update the kiosk settings
ansible-playbook playbook.yml -i inventory.ini --tags kiosk --diff -vv
# First  time you need to be prompted for the password  since the keys are not applied yet
ansible-playbook playbook.yml -i inventory.ini --diff --ask-become-pass -vv

```

Project information
-----------
- The user is the default user 'pi'
- The public_keys are stored in the 'ansible/public_keys' folder. 
- The keys are assigned to the user 'pi' in playbook.yml which must be updated if new keys are added. 

