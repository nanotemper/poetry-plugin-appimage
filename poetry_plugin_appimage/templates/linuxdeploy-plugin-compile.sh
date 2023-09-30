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
"$APPDIR"/usr/bin/python -m compileall "$APPDIR"/usr/app -f -q
"$APPDIR"/usr/bin/python -m compileall "$APPDIR"/usr/conda/lib/python3.7/site-packages/ -f -q || true
