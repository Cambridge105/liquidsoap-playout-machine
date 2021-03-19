# liquidsoap-playout-machine
LiquidSOAP-based playout system for pre-recorded programmes

This repo builds and runs and on-demand playout machine for pre-recorded programmes. The code is designed to spin up the machine only when needed, then destroy it at the end of a period of recorded programmes.

## Getting started
As written, the playout machine is designed to run in AWS EC2, with the machine starting and stopping whenever a recorded programme is required. While most of the code should also be fine with an on-site server, and I've deliberately avoided using DynamoDB databases, for example, some rewriting will be necessary.
To run this machine, you will need to configure the following as well as the scripts in this repo (maybe one day I'll Terraform this but for now we've used the AWS console...):
 
- EC2 instance (we use t3.micro, but t3.nano may suffice) running Ubuntu 20.04. We use AMI ami-08bac620dc84221eb in eu-west-1 (This is created as part of an Auto-Scaling Group as described below)
- S3 bucket containing the pre-recorded material, with object keys following the format yyyymmdd_hhmm_programme-title.mp3 , where the timestamp is the desired playout time. It is recommended to have a lifecycle policy on this to stop it growing and costing money unnecessarily. We delete programmes after 30 days (other copies are kept longer elsewhere).
- Route53 record in a hosted zone, to be updated with the instance IP address
- Settings for the target icecast endpoint stored in SSM Parameter Store, with the mountpoint and password as KMS-encrypted secure strings
- Google Calendar API credentials and token files stored in SSM Parameter Store. The token file is a SecureString. 
- IAM role granting access to S3, Route53, SSM and KMS - see below
- Launch Configuration containing the machine type, security group, IAM role, and the userdata.txt file from this repo added manually
- Auto-Scaling group set to a normal minimum/maximum/desired of 0 instances, pointing to the Launch Configuration
- Schedule on the Auto-Scaling Group, to increase/decrease the ASG desired and minimum sizes when needed (currently done manually, outside the scope of this repo)

![Architecture diagram](https://github.com/Cambridge105/liquidsoap-playout-machine/blob/main/playout.png?raw=true)

## Machine setup
The following tasks are performed by userdata.txt which should be part of the launch configuration. This runs automatically when the EC2 instance is created.
1. Installs required packages, including by running *opamstart.sh*  (See the Code Structure section, below)
2. Clones this repo
3. Gets the credentials and details of the studio stream from Parameter Store and writes them into the config.py file
4. Sets up cron jobs, which will, each hour:
   - copy all today's files from the S3 bucket 
   - run the join30MinFiles.py and checkFilePresent.py scripts (See the Code Structure section, below)
   - then run the makeSchedule.py script (See the Code Structure section, below)
5. Ensures the machine's timezone is set to UK local time, respecting any DST offset
6. Adds all of Rob's and my public keys from GitHub, in addition to the key specified in the Launch Configuration, so either of us can access the machine - Anyone else using this repo will need to add their own public keys instead!
7. Updates DNS with the machine's public IP
8. Gets the credentials to access the schedule Google Calendar from the Parameter Store and writes them to files
9. Runs parseSchedule.py (See the Code Structure section, below)

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

Note on timers: Be aware that the hourly jobs created by *userdata.txt* are cron jobs as they can have best-effort timing. Programmes scheduled by *makeSchedule.py* use systemctl timers with 100 millisecond accuracy. 

## IAM role policy 
The EC2 instance created by the Launch Configuration must have an IAM Role attached, with a Policy granting access to the following (obviously restrict the Resources as required):
- kms:Encrypt (needed because *parseSchedule.py* has to write back the Google Calendar access token as a SecureString to Parameter Store, in case the OAuth Refresh Token has updated)
- kms:Decrypt (needed to decrypt the SecureStrings from Parameter Store, containing the secrets for Icecast and the Google Calendar credentials)
- route53:ChangeResourceRecordSets (needed to update DNS with the public IP of the EC2 instance each time it is launched)
- ssm:GetParameter (needed to get parameter from Parameter Store)
- ssm:GetParametersByPath
- ssm:GetParameters
- ssm:PutParameter (needed to update the OAuth refresh token from Google Calendar's API)
- s3:GetObject (needed to get the pre recorded files from S3)
- s3:ListBucket (needed to get the listing of pre-recorded files in case *checkFilePresent.py* needs to find an older edition)

## Costs
AWS costs for running this infrastructure should be very small, but obviosuly if anyone else uses this code, cost optimisation is their responsibility. The following costs are expected:
- S3 Standard Storage for pre-recorded files (in our case this is around 25GB/month). There are no data transfer costs associated with S3 as we only transfer into S3 and to an EC2 machine in the same region.
- S3 lifecycle policy - negligible
- EC2 on-demand costs - this is optimised as much as possible by only running the instance when required to play a pre-record. Auto-Scaling is free. 
- AWS Parameter Store is free for standard parameters, but there are negligble KMS costs for encryption/decryption of the secure strings
- Route53 - assuming you already have a Hosted Zone to use, the record should be free and DNS queries negligible cost
My rough back-of-envelope calculation suggests this is a maximum of about $6/month in our use-case.
