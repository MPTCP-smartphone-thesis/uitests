#! /bin/bash

# if DEV == 1: relaunch uitest-project all the time
DEV=0

DIR=$(pwd)
[ -n "$1" ] && PROJ_NAME="$1" && shift || read -p "Name of your uitest project? (e.g. 'snapchat') " PROJ_NAME
[ ! -f "$PROJ_NAME/local.properties" ] && NEW_UIPROJ='Y' || read -p "Create new uitest project? [y/N] " NEW_UIPROJ

if [ "$DEV" = "1" -o "$NEW_UIPROJ" = 'Y' -o "$NEW_UIPROJ" = 'y' ]; then
	which android > /dev/null || (echo "Android not found: add it to your PATH" && exit 1) # e.g. PATH=$PATH:/home/quentin/app/android-studio/sdk/tools
	android create uitest-project -n uitests-$PROJ_NAME -t 1 -p uitests-$PROJ_NAME
fi

cd uitests-$PROJ_NAME
ant build || exit 1

which adb > /dev/null || (echo "ADB not found: add it to your PATH" && exit 1)
[ "$(adb devices | wc -l)" -lt 3 ] && echo "Device not connected" && exit 1

cd bin
echo -e "\n\t==== Push the new jar ===="
adb push uitests-$PROJ_NAME.jar  /storage/sdcard0/uitests-$PROJ_NAME.jar || exit 1
cd $DIR

echo -e "\n\t==== Launch the test ===="
adb shell uiautomator runtest /storage/sdcard0/uitests-$PROJ_NAME.jar -c $PROJ_NAME.LaunchSettings $@
