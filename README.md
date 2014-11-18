uitests
=======

Regroup all uitests.

TODO before launching tests:
============================

Of course, you'll need to install all supported apps:

* Dailymotion
* Google Drive: you need a Google account and skip the initial menu (how to use GDrive). You will also need to launch `generate_push_random_seed.sh` script to this file on your phone `/storage/sdcard0/random_seed_orig`
* Facebook: You need to be connected with a Facebook account
* Firefox Beta: Go to Settings / Privacy / Clear Private Data / Always clear when quitting (check that you'll clear everything, you need Firefox 33+)
* Messenger: You need to be connected with a Facebook account and have at least one contact
* Shazam: You need to skip the initial menu
* Snapchat: You need to create this file: `uitests-snapchat/src/login/LoginClass.java` with two `public static` methods which return a `String`: `getUsername()`, `getPassword()`.
* Spotify: You need to be connected with a Spotify account
* Youtube: You need a Google account, skip the initial menu (how to use Youtube)

If you want to use our scripts, you will need to install `adb` (e.g. from `android-tools-adb` package), `ant` and `android` and they should be available without using the full path (available in `$PATH`).

On the device, you will need to install `tcpdump` binary in `/system/xbin/`:

    mount -o remount,rw /system
    cp /PATH/TO/tcpdump /system/xbin/
    chmod 777 /system/xbin/tcpdump
