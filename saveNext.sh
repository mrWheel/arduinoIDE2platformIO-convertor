#!/bin/bash
#
NOW=$(date '+%Y-%m-%d_%H.%M')
echo ${NOW}
SOURCE="${HOME}/tmp/arduinoIDE2platformIO-convertor/next.py"
#DEST="${HOME}/Documents/claudeProgress/next_${NOW}.py"
DEST="${HOME}/Documents/claudeProgress/"
echo "Copy ${SOURCE} to ${DEST}/next_${NOW}.py"
#
cp -v ${SOURCE} ${DEST}/next_${NOW}.py
cp -v ${SOURCE} ../../changes/next_${NOW}.py

echo "Done!"

ls -l ${DEST}

