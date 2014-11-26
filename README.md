uitests
=======

Regroup all uitests.

TODO before launching tests:
============================

Apps
----

Of course, you'll need to install all supported apps:

* Dailymotion: Change the quality to HD.
* Google Drive: You need a Google account and skip the initial menu (how to use GDrive). Then, click on the `upload`, menu on the top right, `settings`, `Display advanced devices`. You will also need to launch `generate_push_random_seed.sh` script to generate this file on your phone `/storage/sdcard0/random_seed_orig`. You need also to go to Settings and uncheck "Transfer files only on Wi-Fi"
* Facebook: You need to be connected with a Facebook account. GPS should be enabled to find the nearest location.
* Firefox Beta: Go to Settings / Privacy / Clear Private Data / Always clear when quitting (check that you'll clear everything, you need Firefox 33+). You also need to install the module `Janus Proxy Configurator`
* Messenger: You need to be connected with a Facebook account and have at least one contact and one previous discussion
* Shazam: You need to skip the initial menu
* Snapchat: You need to create this file: `uitests-snapchat/src/login/LoginClass.java` with two `public static` methods which return a `String`: `getUsername()`, `getPassword()`.
* Spotify: You need to be connected with a Spotify account and need to change the quality to a better one.
* Youtube: You need a Google account, skip the initial menu (how to use Youtube). You also need to go in the menu of YouTube, Settings / General and uncheck "Limit mobile data usage"


On the host machine
-------------------

If you want to use our scripts, you will need to install `adb` (e.g. from `android-tools-adb` package), `ant`, `openjdk-7-jdk`, `git` and `android` and they should be available without using the full path (available in `$PATH`).

You also need to check that you can correctly be connected to the router (or change `CTRL_WIFI` in `launch_tests.py`) via SSH with the parameters set in `launch_tests.py`. You will also need `sshpass` tool

If you want to use `backup_traces.sh`, you need to add an entry `mptcpdata` in `~/.ssh/config` and load your SSH key in your SSH Agent (via ssh-add).


On the device
-------------

Before launching the tests, you need Android 4.4.4 with root rights (all adb commands should be automatically accepted).
You will also need to be a _developer_ and authorize the control from the host machine.

You should remove the lockscreen and not have a too short timeout before going to the sleep mode. If you decide to reboot the phone at the end of the script (`REBOOT` variable), do not lock the SIM card.

You also need to install Multipath Control app and install and setup SSHTunnel to have a MPTCP proxy. You can disable the support of MPTCP in `launch_tests.py`.

You will need to install `tcpdump` binary in `/system/xbin/`:

    mount -o remount,rw /system
    cp /PATH/TO/tcpdump /system/xbin/
    chmod 777 /system/xbin/tcpdump

Note: it's maybe better to not auto-update your apps (Play Store settings) and install adblock (to avoid ads being displayed during the tests).
