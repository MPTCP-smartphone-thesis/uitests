#! /bin/bash
for i in uitests-*; do
    app=${i:8}
    [ -f $i/src/$app/LaunchSettings.java ] || continue
    [ "$app" = "firefox" -o "$app" = "firefoxspdy" ] && file="$i/src/common/FirefoxCommon.java" || file="$i/src/$app/LaunchSettings.java"
    infos=$(sed -e '/Utils\.openApp(/,/)/!d' $file | tr '\n' ' ')
    name=$(echo $infos | cut -d\" -f2)
    pkg=$(echo $infos | cut -d\" -f4)
    act=$(echo $infos | cut -d\" -f6)
    echo "$name - $pkg - $act"
    [ -n "$name" ] && echo $name > $i/app_name.txt
    [ -n "$pkg" ] && echo $pkg > $i/pkg_name.txt
    [ -n "$act" ] && echo $act > $i/act_name.txt
done
