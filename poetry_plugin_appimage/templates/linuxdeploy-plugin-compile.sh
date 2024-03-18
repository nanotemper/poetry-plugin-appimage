#! /bin/bash

set -e

script=$(readlink -f "$0")

show_usage() {
    echo "Usage: $script --appdir <path to AppDir>"
    echo
    echo "Compiles all relevant py files to pyc"
}


APPDIR=

while [ "$1" != "" ]; do
    case "$1" in
        --plugin-api-version)
            echo "0"
            exit 0
            ;;
        --appdir)
            APPDIR="$2"
            shift
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Invalid argument: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
done

# pwd will already be the build directory in tmp
APPDIR_PYTHON="$APPDIR"/usr/bin/python
APPDIR_PYTHON_VERSION=$($APPDIR_PYTHON -c "import sys; print('python{}'.format(sys.version_info.major))")
$APPDIR_PYTHON -m compileall "$APPDIR"/usr/app -f -q
$APPDIR_PYTHON -m compileall "$APPDIR"/usr/conda/lib/$APPDIR_PYTHON_VERSION/site-packages/ -f -q || true
