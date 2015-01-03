#! /bin/bash

dd if=/dev/urandom of=random_seed_orig bs=1 count=800000 || exit 1

which adb > /dev/null || (echo "ADB not found: add it to your PATH" && exit 1)
[ "$(adb devices | wc -l)" -lt 3 ] && echo "Device not connected" && exit 1

adb push random_seed_orig  /storage/sdcard0/random_seed_orig

rm random_seed_orig
