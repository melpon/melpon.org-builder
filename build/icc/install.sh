#!/bin/bash

. ../init.sh

if [ $# -lt 1 ]; then
  echo "$0 <version>"
  exit 0
fi

VERSION=$1
PREFIX=/opt/wandbox/icc-$VERSION

# install

# pip3 install dpcpp-cpp-rt==$VERSION
apt-get update

install_package() {
  apt-get install -y $1=$(apt list -a $1 2>/dev/null | grep -o "$VERSION-[0-9]*" | head -n 1)
}
# install_package intel-oneapi-ippcp-devel
install_package intel-oneapi-compiler-dpcpp-cpp-and-cpp-classic

rm -r $PREFIX || true
cp -r /opt/intel/oneapi/ $PREFIX || true

cp $BASE_DIR/resources/run-icc.sh.in $PREFIX/run-icc.sh
sed -i "s#@icc_prefix@#$PREFIX#g" $PREFIX/run-icc.sh
chmod +x $PREFIX/run-icc.sh

cp $BASE_DIR/resources/run-icc.sh.in $PREFIX/run-icpc.sh
sed -i "s#@icc_prefix@#$PREFIX#g" $PREFIX/run-icpc.sh
chmod +x $PREFIX/run-icpc.sh
