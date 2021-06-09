#!/bin/bash

. ./init.sh

if [ $# -lt 3 ]; then
  echo "$0 <version> <compiler> <compiler_version>"
  exit 0
fi

set -ex

VERSION=$1
COMPILER=$2
COMPILER_VERSION=$3

check_version $VERSION $COMPILER $COMPILER_VERSION

PREFIX=/opt/wandbox/numpy-$VERSION/$COMPILER-$COMPILER_VERSION
COMPILER_PREFIX=/opt/wandbox/$COMPILER-$COMPILER_VERSION

if [ "$COMPILER" = "cpython" ]; then
  export PYTHONPATH=$PREFIX
  $COMPILER_PREFIX/bin/python3 -c 'import numpy; numpy.array([1, 2])'
  test "$($COMPILER_PREFIX/bin/python3 -c 'import numpy; a = numpy.array([1, 2]); print(a)')" = '[1 2]'
else
  exit 1
fi
