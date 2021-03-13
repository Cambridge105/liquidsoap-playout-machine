# liquidsoap-playout-machine
LiquidSOAP-based playout system for pre-recorded programmes

This repo builds and runs and on-demand playout machine for pre-recorded programmes. The code is designed to spin up the machine only when needed, then destroy it at the end of a period of recorded programmes

## Running in AWS
An EC2 t3.micro is plenty big enough (we might even get away with a nano...)
You will need:
* EC2 instance (we use t3.micro) running Ubuntu 20.04. We use AMI ami-08bac620dc84221eb in eu-west-1 
* S3 bucket containing the pre-recorded material, with object keys following the format yyyymmdd_hhmm_programme-title.mp3 , where the timestamp is the playout timestamp
* Route53 record to be updated with the instance IP address
* Settings for the target icecast endpoint stored in SSM Parameter Store, with the mountpoint and password as KMS-encrypted secure strings
* IAM role granting access to S3, Route53, SSM and KMS decryption
* Launch configuration containing the machine type, IAM role, and the userdata.txt file from this repo added manually
* Auto-Scaling group set to a normal minimum/maximum/desired of 0 instances, pointing to the launch configuration
* Scheduled lambda to increase/decrease the ASG desired and minimum sizes when needed (currently outside the scope of this repo)