#!/bin/bash

WDHardwareScriptOnline=0
ACTION="build"
export WDHardwareScriptOnline
#export -p

#env -i
./wdpostinit.sh 


#while true; do
#echo "this is mainProc"
#  echo $WDHardwareScriptOnline
#  sleep 10
#done

RETURN=$?

if [ $RETURN -eq 0 ];
then
  echo "WD Hardware was executed successfuly"
  exit 0
else
  echo "WD Hardware encountered an error while running [$RETURN]"
  exit $RETURN
fi 