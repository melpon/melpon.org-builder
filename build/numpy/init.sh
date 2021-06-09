#!/bin/bash

. ../init.sh

function check_version() {
  version=$1
  compiler=$2
  compiler_version=$3

  while read line; do
    if [ "$version $compiler $compiler_version" = "$line" ]; then
      return 0
    fi
  done < VERSIONS
  return 1
}
