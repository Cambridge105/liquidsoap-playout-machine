#!/usr/bin/python3

import os, datetime, stat 
today = datetime.datetime.today().strftime('%Y%m%d')
directory = "/home/ubuntu/prerecs/"
for filename in os.listdir(directory):
    if filename.endswith(".mp3"): 
        filepath = os.path.join(directory, filename)
        # Is file name representing a time in the past?
        fileyear = filename[:4]
        filemnth = filename[4:6]
        filedate = filename[6:8]
        filehour = filename[9:11]
        filemins = filename[11:13]
        fileplay = datetime.datetime(int(fileyear),int(filemnth),int(filedate),int(filehour),int(filemins))
        if fileplay < datetime.datetime.now():
          continue
        
        # What is the file duration?
        filedur_cmd = 'mp3info -p "%S" ' + filepath + ' > duration.txt'
        os.system(filedur_cmd)
        f = open("duration.txt", "r")
        filedur = f.read()
        filedur = float(filedur)

        if filedur > 2000:
          continue

        if int(filemins) > 29:
          continue

        # We are left with 30 minute files due to play in the first half of the hour
        # Does a 30 min file for the second half of the hour exist?
        target_file = fileyear + filemnth + filedate + "_" + filehour + "3000"
        for testfile in os.listdir(directory):
            if target_file in testfile and testfile.endswith(".mp3"):
                secondfile = directory + testfile
                secondfiledur_cmd = 'mp3info -p "%S" ' + secondfile + ' > duration.txt'
                os.system(secondfiledur_cmd)
                f = open("duration.txt", "r")
                filedur = f.read()
                filedur = float(filedur)
                if filedur > 2000:
                   continue

                # Need to truncate the first file to 30 mins
                os.system("ffmpeg -ss 00:00:00 -t 00:30:00 -i filepath filepath"+"trimmed")
                #Now concatenate first file to second
                os.system("echo \"" + filepath + "trimmed\n" + secondfile + "\"" > filelist.txt)
                os.system("ffmpeg -f concat -safe 0 -i filelist.txt -c copy " + directory + fileyear + filemnth + filedate + "_" + filehour + "0000_joined.mp3")