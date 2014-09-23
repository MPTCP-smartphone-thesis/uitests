DIR=`pwd`
for i in `grep "\[submodule" .gitmodules | cut -d\" -f2`; do
	echo $i
	cd $i
	$@
	cd $DIR
done
