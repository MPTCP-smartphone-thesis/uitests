git pull --recurse-submodules || git pull -u origin master --recurse-submodules
./foreach.sh git pull || ./foreach.sh git pull -u origin master
# git submodule update --remote --recursive
