icehost=$(aws ssm get-parameters --names "/c105-icecast/host" --output text  --query "Parameters[*].{Value:Value}")
iceport=$(aws ssm get-parameters --names "/c105-icecast/port" --output text  --query "Parameters[*].{Value:Value}")
icemount=$(aws ssm get-parameters --names "/c105-icecast/mount" --with-decryption --output text  --query "Parameters[*].{Value:Value}")
icepass=$(aws ssm get-parameters --names "/c105-icecast/password" --with-decryption --output text  --query "Parameters[*].{Value:Value}")
printf 'icehost = \"%s\"\niceport = %s\nicemount=\"%s\"\nicepass=\"%s\"' $icehost $iceport $icemount $icepass | sed '1h;1!H;$!d;x;s/\r/''/g' | cat -v > config.py