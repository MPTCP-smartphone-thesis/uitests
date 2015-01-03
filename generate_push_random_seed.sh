#! /bin/bash

for i in $(seq 0 9); do
    dd if=/dev/urandom of=random_seed_orig_$i bs=1 count=99999
done || exit 1

which adb > /dev/null || (echo "ADB not found: add it to your PATH" && exit 1)
[ "$(adb devices | wc -l)" -lt 3 ] && echo "Device not connected" && exit 1

for i in $(seq 0 9); do
    adb push random_seed_orig_$i  /storage/sdcard0/
done

rm random_seed_orig_*
