#! /bin/bash
for i in uitests-*; do
    app=${i:8}
    [ -f $i/src/$app/LaunchSettings.java ] || continue
    [ "$app" = "firefox" -o "$app" = "firefoxspdy" ] && file="$i/src/common/FirefoxCommon.java" || file="$i/src/$app/LaunchSettings.java"
    name=$(grep "Utils\.openApp" $file | cut -d\" -f2)
    pkg=$(grep "Utils\.openApp" $file | cut -d\" -f4)
    echo "$name - $pkg"
    [ -n "$name" ] && echo $name > $i/app_name.txt
    [ -n "$pkg" ] && echo $pkg > $i/pkg_name.txt
done
