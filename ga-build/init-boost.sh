# boost/run.sh から source で呼ばれるスクリプト。
# このスクリプトを直接呼ぶことは無い。
set -e

TARGET=$(basename `pwd`)

. ../init.sh

if [ $# -lt 1 ]; then
  echo "$0 <subcommand> [args...]"
  exit 0
fi

SUBCOMMAND=$1
if [ $SUBCOMMAND == "install" ]; then
  if [ $# -lt 4 ]; then
    echo "$0 <subcommand> <version> <compiler> <compiler_version>"
    exit 1
  fi

  VERSION=$2
  COMPILER=$3
  COMPILER_VERSION=$4
  PACKAGE_FILENAME=$TARGET-$VERSION-$COMPILER-$COMPILER_VERSION.tar.gz
  PACKAGE_PATH=/opt/wandbox/$TARGET-$VERSION-$COMPILER-$COMPILER_VERSION.tar.gz
  PREFIX=/opt/wandbox/$TARGET-$VERSION-$COMPILER-$COMPILER_VERSION
fi

case "$SUBCOMMAND" in
  "setup" ) : ;;
  "install" ) : ;;
  * ) exit 1
esac

check_install $PACKAGE_FILENAME

set -x