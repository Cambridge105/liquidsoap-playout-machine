#!/bin/bash
set -e
if ! sudo -n true; then
	echo "Cannot run sudo without password"
	exit 1
fi
sudo apt-get update
sudo apt-get upgrade -y
sudo apt install awscli -y
mkdir /home/ubuntu/prerecs/
sudo apt-get install build-essential software-properties-common -y
sudo add-apt-repository ppa:avsm/ppa -y
sudo apt install opam -y
cd /home/ubuntu/
git clone https://github.com/Cambridge105/liquidsoap-playout-machine.git
sudo apt-get install mp3info -y
sudo apt-get install ffmpeg -y
sudo apt install python3-pip -y
cd /home/ubuntu/prerecs
sudo chown -R ubuntu:ubuntu /home/ubuntu/
sudo rm /etc/localtime
sudo ln -s /usr/share/zoneinfo/Europe/London /etc/localtime
/bin/bash /home/ubuntu/liquidsoap-playout-machine/opamstart.sh
/bin/bash /home/ubuntu/liquidsoap-playout-machine/makeConfig.sh

make_timer () {
	local timer_name=$1
	local exec_command=$2
	local calendar_string=$3

	cat << EOF | sudo tee /etc/systemd/system/${timer_name}.timer
[Unit]
Description=${timer_name} timer

[Timer]
OnCalendar=${calendar_string}
Persistent=false
AccuracySec=100ms

[Install]
WantedBy=timers.target
EOF
	cat << EOF | sudo tee /etc/systemd/system/${timer_name}.service
[Unit]
Description=${timer_name} service

[Service]
Type=oneshot
ExecStart=${exec_command}
User=ubuntu
Group=ubuntu
EOF
	sudo systemctl daemon-reload
	sudo systemctl enable ${timer_name}.timer
	sudo systemctl start ${timer_name}.timer
}

# Clear out any old LS files - both historical and where the future schedule may have changed PID for a slot
# Only do this once a day when we aren't live in case deleting a file that's currently playing upsets LS
make_timer "tidy-old-liqs" "/bin/rm /home/ubuntu/prerecs/*.liq" "04:40:00"

# Grab the schedule from Google Calendar and turn it into a CSV
make_timer "parse-schedule" "/usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/parseSchedule.py" "*:45:00"

# Sync pre-recs from S3
make_timer "sync-prerecs" "/usr/bin/aws s3 sync s3://cambridge105-co-uk-prerecs /home/ubuntu/prerecs --include \"*.mp3\" --exclude \"*.liq\" --delete" "*:48:00"

# Join any half-hour shows into full-hour files
make_timer "join-30mins" "/usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/join30MinFiles.py" "*:50:00"

# Fill in any missing recordings with repeats
make_timer "check-file-present" "/usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/checkFilePresent.py" "*:52:00"

# Create the Liquidsoap files for the schedule
make_timer "make-schedule" "/usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/makeSchedule.py" "*:53:00"

# Import SSH pubkeys
if [ ! -d /home/ubuntu/.ssh ]; then
	mkdir -p /home/ubuntu/.ssh
fi
wget https://github.com/dnas2.keys -O ->> /home/ubuntu/.ssh/authorized_keys
wget https://github.com/rmc47.keys -O ->> /home/ubuntu/.ssh/authorized_keys

# Install required utilities
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib boto3
pip3 install --upgrade awscli

# Limit how many S3 transfers to do in parallel, to avoid swamping the internet connection
aws configure set default.s3.max_concurrent_request 1

# Grab the Google calendar credentials
aws ssm get-parameters --region "eu-west-1" --names "/c105-icecast/gcal-credentials" --output text  --query "Parameters[*].{Value:Value}" > /home/ubuntu/liquidsoap-playout-machine/credentials.json
aws ssm get-parameters --region "eu-west-1" --names "/c105-icecast/gcal-token" --with-decryption --output text  --query "Parameters[*].{Value:Value}" > /home/ubuntu/liquidsoap-playout-machine/token.json

# Initial parse of the schedule
python3 /home/ubuntu/liquidsoap-playout-machine/parseSchedule.py
sudo chown ubuntu:ubuntu /home/ubuntu/schedule.csv

# Set up the playout timer
sudo cp /home/ubuntu/liquidsoap-playout-machine/liquidsoap-playout.service /etc/systemd/system/
sudo cp /home/ubuntu/liquidsoap-playout-machine/liquidsoap-playout.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable liquidsoap-playout.timer
sudo systemctl start liquidsoap-playout.timer