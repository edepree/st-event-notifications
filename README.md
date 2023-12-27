# st-event-notifications
A simple notification workflow for Slightly Toasted events

# Setup
This script was configured/tested on an Ubuntu 22.04 endpoint

## Install Operating System Level Dependencies
```bash
sudo apt install python3-dev python3-venv firefox
```

## Python Environment Setup
Download the project (e.g. `git clone https://github.com/edepree/st-event-notifications.git`) and setup the virtual environment within the project itself.

```bash
cd st-event-notifications
python3 -m venv .venv
source .venv/bin/activate
pip install selenium
```

## Configure Scheduling
Using a cron job one can access the crontab (e.g. `crontab -e`) and configure the script to run every six hours. In the below example the cron job first changes its directory to project folder so relative pathing may be used.

```bash
0 */6 * * * cd /home/ubuntu/st-event-notifications && .venv/bin/python3 st-event-notifications.py --unattended -u "CHANGE_ME" -p "CHANGE_ME" -s "CHANGE_ME" -r "CHANGE_ME"
```
