# liquidsoap-playout-machine
LiquidSOAP-based playout system for pre-recorded programmes

This repo builds and runs and on-demand playout machine for pre-recorded programmes. The code is designed to spin up the machine only when needed, then destroy it at the end of a period of recorded programmes.

## Getting started
As written, the playout machine is designed to run in AWS EC2, with the machine starting and stopping whenever a recorded programme is required. While most of the code should also be fine with an on-site server, and I've deliberately avoided using DynamoDB databases, for example, some rewriting will be necessary.
To run this machine, you will need to configure the following as well as the scripts in this repo (maybe one day I'll Terraform this but for now we've used the AWS console...):
 
- EC2 instance (we use t3.micro, but t3.nano may suffice) running Ubuntu 20.04. We use AMI ami-08bac620dc84221eb in eu-west-1 
- S3 bucket containing the pre-recorded material, with object keys following the format yyyymmdd_hhmm_programme-title.mp3 , where the timestamp is the desired playout time
- Route53 record in a hosted zone, to be updated with the instance IP address
- Settings for the target icecast endpoint stored in SSM Parameter Store, with the mountpoint and password as KMS-encrypted secure strings
- Google Calendar API credentials and token files stored in SSM Parameter Store. The token file is a SecureString. 
- IAM role granting access to S3, Route53, SSM and KMS decryption
- Launch configuration containing the machine type, IAM role, and the userdata.txt file from this repo added manually
- Auto-Scaling group set to a normal minimum/maximum/desired of 0 instances, pointing to the launch configuration
- Schedule on the Auto-Scaling group, to increase/decrease the ASG desired and minimum sizes when needed (currently done manually, outside the scope of this repo)

## Code structure
The code is formed of a number of scripts:

 - *checkFilePresent.py* - This runs just before each hour and compares a cached copy of the schedule (*schedule.csv*) to the available files. If a recorded programme is scheduled for the next hour but there is no file, it finds a previous edition of the programme from the source folder so it has something to play.
 - *join30MinFiles.py* - This runs just before each hour and checks whether the following hour contains two 30 minute programmes. It uses the available files, not the schedule, to check this. If there are two 30 minute files, the first to run is truncated to exactly 30 minutes if it is fractionally over and then the second file is concatenated to the first, forming a file called *yyyymmdd_hh00_joined.mp3* 
 -  *makeConfig.py* - This runs at boot and creates a file called config.py, which contains secrets that aren't in the public git repo
 - *makeSchedule.py* - This is the main task. It runs just before each hour and checks the available files to see what recorded programmes are available. For each MP3 file, it creates a corresponding Liquidsoap script to send the file to an Icecast server (using credentials and settings in *config.py*) at the appropriate time. It then creates a systemctl timer to run the Liquidsoap script. Note that this is independent of the schedule itself, so it will still work if the schedule link breaks. If a *_joined.mp3* file (created by *join30MinFiles.py*) is present as well as two 30 minute files for the same hour, the *_joined.mp3* file is used. Obviously, each hour both *checkFilePresent.py* and *join30MinFiles.py* must run before *makeSchedule.py*
 - *opamstart.sh* - This is run at boot to install additional OPAM components
 - *parseSchedule.py* - This is run at boot. It connects to Google Calendar to download the schedule, using credentials which are also fetched during boot. It writes *schedule.csv*, which contains recorded programmes scheduled today and tomorrow. This schedule information is used by *checkFilePresent.py*
 - *update-route53-A.json* - This is a template config script used to update DNS with the machine's public IP at boot.
 - *userdata.txt* - This contains the machine setup and configuration and is designed to be used as part of a launch template in AWS. 
