#!/usr/bin/python3

import os, datetime, stat
import config

today = datetime.datetime.today().strftime('%Y%m%d')
directory = "/home/ubuntu/prerecs/"
crontab = "SHELL=/bin/sh\nPATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n"
crontab = crontab + "50 6-22 * * * aws s3 sync s3://cambridge105-co-uk-prerecs /home/ubuntu/prerecs --exclude \"*.mp3\" --include \"" + today + "*\" \n"
crontab = crontab + "52 6-22 * * * /usr/bin/python3 /home/ubuntu/liquidsoap-playout-machine/makeSchedule.py\n"
crontab = crontab + "53 6-22 * * * crontab /home/ubuntu/crontab\n"
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
        cronexp = filemins + " " + filehour + " " + filedate + " " + filemnth + " * "

        # What is the file duration?
        filedur_cmd = 'mp3info -p "%S" ' + filepath + ' > duration.txt'
        os.system(filedur_cmd)
        f = open("duration.txt", "r")
        filedur = f.read()
        filedur = float(filedur)

        # Set the max_duration to a limited amount
        if filedur < 13000:
           maxdur = 12592.0
        if filedur < 11000:
           maxdur = 10725.0
        if filedur < 9120:
           maxdur = 8992.0
        if filedur < 8000:
           maxdur = 7125.0
        if filedur < 6000:
           maxdur = 5392.0
        if filedur < 4000:
           maxdur = 3525.0
        if filedur < 2000:
           maxdur = 1792.0

        # Write the liquidsoap for the file
        ls = "source = once(single(\"" + filepath + "\"))\n"
        ls = ls + "output.icecast(%opus(vbr=\"none\",application=\"audio\",bitrate=256,stereo,signal=\"music\"), host=\"" + config.icehost + "\", port=" + config.iceport + ", password=\"" + config.icepass + "\", mount=\"" + config.icemount + "\", fallible=true, on_stop=shutdown, max_duration(" + str(maxdur) + ",source))\n"
        ls = ls + "output.dummy(blank())"

        lsfile = open("/home/ubuntu/prerecs/" + filename + ".liq","w")
        lsfile.write(ls)
        lsfile.close()
        st = os.stat("/home/ubuntu/prerecs/" + filename + ".liq")
        os.chmod("/home/ubuntu/prerecs/" + filename + ".liq", st.st_mode | stat.S_IEXEC)

        crontab = crontab + cronexp + "(. ~/.bash_profile; /home/ubuntu/.opam/default/bin/liquidsoap /home/ubuntu/prerecs/" + filename + ".liq)\n"
        continue
    else:
        continue

cron = open("/home/ubuntu/crontab","w")
cron.write(crontab)
cron.close()
