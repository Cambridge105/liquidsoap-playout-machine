#!/bin/bash
source /home/ubuntu/.bash_profile
# Caculate the prefix that would exist for this playout slot if it's a pre-rec
# Assumption: we never fire before the top of the hour, and all slots start on the hour
TIME_PREFIX=$(date +"%Y%m%d_%H00")
# Find, if available, a liquidsoap file for this slot
# Assumption: there will be no more than one liquidsoap file. This should hold true
# as long as there aren't any within-day schedule changes after the original file
# has been uploaded
PLAYOUT_TARGET=$(ls /home/ubuntu/prerecs/$TIME_PREFIX*.liq | head -n 1)
# If there is one, play it!
if [ -f $PLAYOUT_TARGET ]; then
	# Run the long-running task asynchronously, so this service isn't considered
	# still running when the timer next goes off - or it gets queued up
	# for when liquidsoap does exit
	systemd-run --uid=ubuntu /home/ubuntu/.opam/default/bin/liquidsoap $PLAYOUT_TARGET
fi