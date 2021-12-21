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
        filedur_cmd = 'mp3info -p "%S" ' + filepath + ' > /tmp/duration.txt'
        os.system(filedur_cmd)
        f = open("/tmp/duration.txt", "r")
        filedur = f.read()
        filedur = float(filedur)

        # Set the max_duration to a limited amount
        if filedur < 13000:
           maxdur = 12592.0
           fadeout_dur = 12592
        if filedur < 11000:
           maxdur = 10725.0
           fadeout_dur = 10712
        if filedur < 9120:
           maxdur = 8992.0
           fadeout_dur = 8992
        if filedur < 8000:
           maxdur = 7125.0
           fadeout_dur = 7112
        if filedur < 6000:
           maxdur = 5392.0
           fadeout_dur = 5392
        if filedur < 4000:
           maxdur = 3525.0
           fadeout_dur = 3512
        if filedur < 2000:
           maxdur = 1792.0
           fadeout_dur = 1792

        if filedur < 2000:
           if os.path.isfile(directory + fileyear + filemnth + filedate + "_" + filehour + "00_joined.mp3"):
               # The hour has two 30 min programmes which are already joined, so we need to schedule that instead of this original file
               continue		   

        # Write the liquidsoap for the file
        ls = "source = once(single(\"" + filepath + "\"));\ndef cue_meta(m) =\n        [(\"liq_cue_in\",\"0\"),(\"liq_cue_out\",\"" + str(fadeout_dur) + "\")]\nend\nsource = map_metadata(cue_meta,source)\nsource = fade.out(cue_cut(source))\n"
        ls = ls + "output.icecast(%opus(vbr=\"none\",application=\"audio\",bitrate=256,stereo,signal=\"music\"), host=\"" + config.icehost + "\", port=" + config.iceport + ", password=\"" + config.icepass + "\", mount=\"" + config.icemount + "\", fallible=true, on_stop=shutdown, max_duration(" + str(maxdur) + ",source))\n"
        ls = ls + "output.dummy(blank())"

        lsfile = open("/home/ubuntu/prerecs/" + filename + ".liq","w")
        lsfile.write(ls)
        lsfile.close()
        st = os.stat("/home/ubuntu/prerecs/" + filename + ".liq")
        os.chmod("/home/ubuntu/prerecs/" + filename + ".liq", st.st_mode | stat.S_IEXEC)

        continue
    else:
        continue


