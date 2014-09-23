#! /bin/bash

DIR=$(pwd)
read -p "Name of your uitest project? (e.g. 'snapchat') " PROJ_NAME
read -p "Create new uitest project? [y/N] " NEW_UIPROJ

if [ "$NEW_UIPROJ" = 'Y' -o "$NEW_UIPROJ" = 'y' ]; then
	which android > /dev/null || (echo "Android not found: add it to your PATH" && exit 1) # e.g. PATH=$PATH:/home/quentin/app/android-studio/sdk/tools
	android create uitest-project -n uitests-$PROJ_NAME -t 1 -p uitests-$PROJ_NAME
fi

cd uitests-$PROJ_NAME
ant build || exit 1
cd bin
adb push uitests-$PROJ_NAME.jar  /storage/sdcard0/uitests-$PROJ_NAME.jar || exit 1
cd $DIR

read -p "Do you want to launch it? [Y/n] " UI_LAUNCH
[ "$UI_LAUNCH" != "n" -a "$UI_LAUNCH" != "N" ] && adb shell uiautomator runtest /storage/sdcard0/uitests-$PROJ_NAME.jar -c $PROJ_NAME.LaunchSettings
