#!/usr/bin/python3

import os, datetime, stat
import config

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

        if filedur < 2000:
           if os.path.isfile(directory + fileyear + filemnth + filedate + "_" + filehour + "00_joined.mp3"):
               # The hour has two 30 min programmes which are already joined, so we need to schedule that instead of this original file
               continue		   

        # Write the liquidsoap for the file
        ls = "source = once(single(\"" + filepath + "\"))\n"
        ls = ls + "output.icecast(%opus(vbr=\"none\",application=\"audio\",bitrate=256,stereo,signal=\"music\"), host=\"" + config.icehost + "\", port=" + config.iceport + ", password=\"" + config.icepass + "\", mount=\"" + config.icemount + "\", fallible=true, on_stop=shutdown, max_duration(" + str(maxdur) + ",source))\n"
        ls = ls + "output.dummy(blank())"

        lsfile = open("/home/ubuntu/prerecs/" + filename + ".liq","w")
        lsfile.write(ls)
        lsfile.close()
        st = os.stat("/home/ubuntu/prerecs/" + filename + ".liq")
        os.chmod("/home/ubuntu/prerecs/" + filename + ".liq", st.st_mode | stat.S_IEXEC)

        systemd_timer = "[Unit]\nDescription=Playout for " + filename + "\n\n[Timer]OnCalendar=" + fileyear + "-" + filemnth + "-" + filedate + " " + filehour + ":" + filemins + ":00\nPersistent=false\nAccuracySec=100ms\n\n[Install]\nWantedBy=timers.target"
        systemd_timer_file = open("/home/ubuntu/playout" + filedate + filehour + filemins + ".timer")
        systemd_timer_file.write(systemd_timer)
        systemd_timer_file.close()
        os.system("sudo mv /home/ubuntu/playout" + filedate + filehour + filemins + ".timer /etc/systemd/system/playout" + filedate + filehour + filemins + ".timer")
        
        command = "/usr/bin/bash ~/.bash_profile; /home/ubuntu/.opam/default/bin/liquidsoap /home/ubuntu/prerecs/" + filename + ".liq"
        systemd_service = "[Unit]\nDescription=Playout for " + filename + "\n\n[Service]\nType=oneshot\nExecStart=" + command + "\nUser=ubuntu\nGroup=ubuntu"
        systemd_service_file = open("/home/ubuntu/playout" + filedate + filehour + filemins + ".service")
        systemd_service_file.write(systemd_service)
        systemd_service_file.close()
        os.system("sudo mv /home/ubuntu/playout" + filedate + filehour + filemins + ".service /etc/systemd/system/playout" + filedate + filehour + filemins + ".service")
        
        
        os.system("sudo systemctl daemon-reload")
        os.system("sudo systemctl start playout" + filedate + filehour + filemins + ".timer")


        continue
    else:
        continue


