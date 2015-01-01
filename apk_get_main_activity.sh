#!/bin/bash
[ "$1" = "" -a ! -f "$1" ] && echo "No APK as first argument"

if [ $(which aapt > /dev/null) ]; then
    AAPT="aapt"
else # aapt not avaible, check on PATH
    IFS=':'; for i in $PATH; do
        if [[ "$i" == *"/sdk/tools" ]]; then
            BUILD_DIR="${i:0:-5}build-tools"
            AAPT=$(echo $BUILD_DIR/*/aapt | tail -n 1)
            [ -f "$AAPT" ] && break
            unset AAPT
        fi
    done
fi
[ -z "$AAPT" ] && echo "'aapt' not in your PATH" && exit 1

AAPT_DUMP=$($AAPT dump badging $1 || exit 1)

# http://stackoverflow.com/a/17289998
PKG_NAME=$(echo $AAPT_DUMP | awk -F" " '/package/ {print $2}' | awk -F"'" '/name=/ {print $2}')
ACTIVITY=$(echo $AAPT_DUMP | awk -F" " '/launchable-activity/ {print $2}' | awk -F"'" '/name=/ {print $2}')

echo "package name:  $PKG_NAME"
echo "main activity: $ACTIVITY"
