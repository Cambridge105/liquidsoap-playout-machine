#!/usr/bin/python3
import datetime
import os
from boto3 import client
from botocore.config import Config

#TODO: Handle half hour progs at :30

my_config = Config(region_name='eu-west-1')

f = open("/home/ubuntu/schedule.csv","r")
schedule = f.read()
f.close()

timeNow = datetime.datetime.now(datetime.timezone.utc).astimezone()
nextHour = timeNow + datetime.timedelta(hours=1)
nextHourISO = nextHour.strftime("%Y-%m-%dT%H:00:00%z")
if "+0100" in nextHourISO:
    nextHourISO = nextHourISO.replace("+0100","+01:00") #because you'd think a standard was a standard...
print("Next hour " + nextHourISO)
fileToCheck = ''

programmes = schedule.splitlines()
for programme in programmes:
    programInfo = programme.split(",")
    if programInfo[0] == '"' + nextHourISO + '"':
        fileToCheck = '/home/ubuntu/prerecs/' + programInfo[3].replace('"','') + '.mp3'
        print(fileToCheck)
 
        if len(fileToCheck) > 1:
            if os.path.isfile(fileToCheck):
                quit()

        conn = client('s3',config=my_config) 
        fileToUse = '' 
        for key in conn.list_objects(Bucket='cambridge105-co-uk-prerecs')['Contents']:
            objectKey = key['Key'].split("_")
            if (len(objectKey)<3):
                continue
            objectKey[2] = objectKey[2].replace(".mp3","")
            if objectKey[2] == programInfo[2].replace('"',''): 
                fileToUse = key['Key']
        if len(fileToUse)>0:
            os.system("aws s3 cp s3://cambridge105-co-uk-prerecs/" + fileToUse + " /home/ubuntu/prerecs/" + nextHour.strftime("%Y%m%d_%H00") + "_" + programInfo[2].replace('"','') + ".mp3")
            quit()
        print("Bad")

