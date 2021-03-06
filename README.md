uitests
=======

Regroup all uitests. This code is part of the Master Thesis [Multipath TCP with Real Smartphone Applications ](http://dial.uclouvain.be/memoire/ucl/object/thesis:366) by [Matthieu Baerts](https://github.com/matttbe) and [Quentin De Coninck](https://github.com/qdeconinck).

TODO before launching tests:
============================

Apps
----

Of course, you'll need to install all supported apps:

* Dailymotion: Change the quality to HD. Disable the option "only download on WiFi". Check the box "Sync in HD when available". Follow one video channel (where the videos will be taken). The version tested is 4.3.2.
* Dropbox: You will need to sign up/in, skip the welcome screen (no need to turn on camera upload option) and send at least one file that you can delete just after. The tested version is 2.4.6.8.
* Google Drive: You need a Google account and skip the initial menu (how to use GDrive). Then, click on the `upload`, menu on the top right, `settings`, `Display advanced devices`. You need also to go to Settings and uncheck "Transfer files only on Wi-Fi". The tested version is 2.0.222.51.
* Facebook: You need to be connected with a Facebook account. GPS should be enabled to find the nearest location. The tested version is 17.0.0.23.16.
* Firefox Beta: Go to Settings / Privacy / Clear Private Data / Always clear when quitting (check that you'll clear everything, you need Firefox 33+). You also need to install the module `Janus Proxy Configurator`. If you want to setup your own Janus server, you can use this Docker image [here](https://registry.hub.docker.com/u/matttbe/docker-janus-node/) (don't forget to generate a new SSL key and accept it on your Android device as written in the `README` file). The tested version is 33.0.
* Messenger: You need to be connected with a Facebook account and have at least one contact and one previous discussion. The tested version is 13.0.0.19.13.
* Shazam: You need to skip the initial menu
* Snapchat: You need to create this file: `Login.java` with two `public static` methods which return a `String`: `getUsername()`, `getPassword()`, e.g.: have a lookt to `LoginSample.java` file.
* Spotify: You need to be connected with a Spotify account and need to change the quality to a better one. The tested version is 1.5.0.739.
* Youtube: You need a Google account, skip the initial menu (how to use Youtube). You also need to go in the menu of YouTube, Settings / General and uncheck "Limit mobile data usage". The tested version is 5.10.3.5.


On the host machine
-------------------

If you want to use our scripts, you will need to install `adb` (e.g. from `android-tools-adb` package), `openjdk-7-jdk`, `git`, `ant` and `android` (from the Android SDK) and they should be available without using the full path (available in `$PATH`).

You also need to check that you can correctly be connected to the router (or change `CTRL_WIFI` in `launch_tests.py`) via SSH with the parameters set in `launch_tests.py`. You will also need `sshpass` tool. If you're using a proxy, it can be interesting to change `EXT_HOST` variable.

If you want to use `backup_traces.sh`, you need to add an entry `mptcpdata` in `~/.ssh/config` and load your SSH key in your SSH Agent (via ssh-add).


On the device
-------------

Before launching the tests, you need Android 4.4.4 with root rights (all adb commands should be automatically accepted).
You will also need to be a _developer_ and authorize the control from the host machine.

You should remove the lockscreen and not have a too short timeout before going to the sleep mode. If you decide to reboot the phone at the end of the script (`REBOOT` variable), do not lock the SIM card.

You also need to install Multipath Control app, Busybox (and install binaries) and setup SSHTunnel or ShadowSocks to have a MPTCP capable proxy. Note that you can disable the support of MPTCP in `launch_tests.py` and then these three apps will no longer be needed.

You will need to install `tcpdump` binary in `/system/xbin/`:

    mount -o remount,rw /system
    cp /PATH/TO/tcpdump /system/xbin/
    chmod 777 /system/xbin/tcpdump

Note that it's maybe better to not auto-update your apps (Play Store settings) and install adblock (to avoid ads being displayed during the tests).

For Dropbox and Drive, you will also need to launch `generate_push_random_seed.sh` script to generate these files on your phone `/storage/sdcard0/a_random_seed_orig_*`.

If you want to use `net.iproute_set_multipath*()` methods (or `WITH_MPTCP_BACKUP`), you will need to recompile iproute2: https://github.com/MPTCP-smartphone-thesis/android-iproute2


On the (controlled) router
--------------------------

`launch_tests.py` script can control the router to add delay/losses. This router should has a ssh server (don't forget to connect to it one to avoid 'trust' questions) and Netem module (`tc` command) has to be installed (`sch_netem`/`kmod-sched` packages) and enabled (check with `lsmod`). If you want to limit bandwidth on the router, you'll need to also install WShaper (and set `LIMIT_BW_WSHAPER_SUPPORTED` to `True`).


`launch_tests.py` script
========================

Some constant are used on the top of the script. If you want to change it, feel free to rewrite them `launch_tests_conf.py` file (next to `launch_tests.py` file).
