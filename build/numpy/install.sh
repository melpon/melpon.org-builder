#!/bin/bash

. ./init.sh

if [ $# -lt 3 ]; then
  echo "$0 <version> <compiler> <compiler_version>"
  exit 0
fi

VERSION=$1
COMPILER=$2
COMPILER_VERSION=$3

check_version $VERSION $COMPILER $COMPILER_VERSION

PREFIX=/opt/wandbox/numpy-$VERSION/$COMPILER-$COMPILER_VERSION
COMPILER_PREFIX=/opt/wandbox/$COMPILER-$COMPILER_VERSION
VERSION_TARNAME=$(echo $VERSION | sed 's/\./_/g')

$COMPILER_PREFIX/bin/python3 -m pip install -U pip
$COMPILER_PREFIX/bin/python3 -m pip install -t $PREFIX numpy==$VERSION
