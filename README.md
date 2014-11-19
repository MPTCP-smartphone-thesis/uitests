uitests
=======

Regroup all uitests.

TODO before launching tests:
============================

Apps
----

Of course, you'll need to install all supported apps:

* Dailymotion: Change the quality to HD.
* Google Drive: You need a Google account and skip the initial menu (how to use GDrive). You will also need to launch `generate_push_random_seed.sh` script to this file on your phone `/storage/sdcard0/random_seed_orig`
* Facebook: You need to be connected with a Facebook account
* Firefox Beta: Go to Settings / Privacy / Clear Private Data / Always clear when quitting (check that you'll clear everything, you need Firefox 33+)
* Messenger: You need to be connected with a Facebook account and have at least one contact
* Shazam: You need to skip the initial menu
* Snapchat: You need to create this file: `uitests-snapchat/src/login/LoginClass.java` with two `public static` methods which return a `String`: `getUsername()`, `getPassword()`.
* Spotify: You need to be connected with a Spotify account and need to change the quality to a better one.
* Youtube: You need a Google account, skip the initial menu (how to use Youtube)


On the host machine
-------------------

If you want to use our scripts, you will need to install `adb` (e.g. from `android-tools-adb` package), `ant` and `android` and they should be available without using the full path (available in `$PATH`).

You also need to check that you can correctly be connected to the router (or change `CTRL_WIFI` in `launch_tests.py`) via SSH with the parameters set in `launch_tests.py`.


On the device
-------------

Before launching the tests, you need Android 4.4.4 with root rights (all adb commands should be automatically accepted).
You will also need to be a _developer_ and authorize the control from the host machine.

You should remove the lockscreen and not have a too short timeout before going to the sleep mode. If you decide to reboot the phone at the end of the script (`REBOOT` variable), do not lock the SIM card.

You will need to install `tcpdump` binary in `/system/xbin/`:

    mount -o remount,rw /system
    cp /PATH/TO/tcpdump /system/xbin/
    chmod 777 /system/xbin/tcpdump

Note: it's maybe better to not auto-update your apps (Play Store settings) and install adblock (to avoid ads being display during the tests).
