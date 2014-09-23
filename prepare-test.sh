if [ "$2" == 'Y' ]; then
cd ~/app/android-studio/sdk/tools
./android create uitest-project -n uitests-$1 -t 1 -p /home/quentin/MPTCP/Git/uitests/uitests-$1
fi
cd ~/MPTCP/Git/uitests/uitests-$1
ant build
cd bin
adb push uitests-$1.jar  /storage/sdcard0/uitests-$1.jar
