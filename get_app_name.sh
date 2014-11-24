#! /bin/bash
for i in uitests-*; do
    app=${i:8}
    [ -f $i/src/$app/LaunchSettings.java ] || continue
    name=$(grep "Utils\.openApp" $i/src/$app/LaunchSettings.java | cut -d\" -f2)
    echo $name
    [ -n "$name" ] && echo $name > $i/app_name.txt
done
