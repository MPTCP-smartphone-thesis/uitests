uitests
=======

Regroup all uitests.

TODO before launching tests:
============================

Of course, you'll need to install all supported apps:

* Dailymotion
* Google Drive: you need a Google account and skip the initial menu. You will also need to launch `generate_push_random_seed.sh` script to this file on your phone `/storage/sdcard0/random_seed_orig`
* Facebook: You need to be connected with a Facebook account
* Firefox Beta: Go to Parameter / Private Life / Clear Private Data / Always clear when quitting (check that you'll clear everything, you need Firefox 33+)
* Messenger: You need to be connected with a Facebook account and have at least one contact
* Shazam
* Snapchat: You need to create this file: `uitests-snapchat/src/login/LoginClass.java` with two `public static` methods which return a `String`: `getUsername()`, `getPassword()`.
* Spotify
* Youtube

If you want to use our scripts, you will need to install `adb` (e.g. from `android-tools-adb` package), `ant` and `android` and they should be available without using the full path (available in `$PATH`).
