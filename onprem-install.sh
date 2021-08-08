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
sudo apt-get install build-essential -y
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
# Clear out any old LS files - both historical and where the future schedule may have changed PID for a slot
# Only do this once a day when we aren't live in case deleting a file that's currently playing upsets LS
echo '40 4 * * * /bin/rm /home/ubuntu/prerecs/*.liq' > /tmp/mycrontab
echo '45 * * * * /usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/parseSchedule.py' >> /tmp/mycrontab
echo '48 * * * * /usr/bin/aws s3 sync s3://cambridge105-co-uk-prerecs /home/ubuntu/prerecs --include "*.mp3" --exclude "*.liq" --delete' >> /tmp/mycrontab
echo '50 * * * * /usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/join30MinFiles.py' >> /tmp/mycrontab
echo '52 * * * * /usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/checkFilePresent.py' >> /tmp/mycrontab
echo '53 * * * * /usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/makeSchedule.py' >> /tmp/mycrontab
crontab -u ubuntu /tmp/mycrontab
wget https://github.com/dnas2.keys -O ->> /home/ubuntu/.ssh/authorized_keys
wget https://github.com/rmc47.keys -O ->> /home/ubuntu/.ssh/authorized_keys
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib boto3
pip3 install --upgrade awscli
aws ssm get-parameters --region "eu-west-1" --names "/c105-icecast/gcal-credentials" --output text  --query "Parameters[*].{Value:Value}" > /home/ubuntu/liquidsoap-playout-machine/credentials.json
aws ssm get-parameters --region "eu-west-1" --names "/c105-icecast/gcal-token" --with-decryption --output text  --query "Parameters[*].{Value:Value}" > /home/ubuntu/liquidsoap-playout-machine/token.json
python3 /home/ubuntu/liquidsoap-playout-machine/parseSchedule.py
sudo chown ubuntu:ubuntu /home/ubuntu/schedule.csv
sudo cp /home/ubuntu/liquidsoap-playout-machine/liquidsoap-playout.service /etc/systemd/system/
sudo cp /home/ubuntu/liquidsoap-playout-machine/liquidsoap-playout.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable liquidsoap-playout.timer
sudo systemctl start liquidsoap-playout.timer