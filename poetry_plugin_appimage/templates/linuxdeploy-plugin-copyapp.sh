#! /bin/bash

# One solution to deploy application sources to the AppDir. It follows linuxdeploy spec (version 1)

set -e

script=$(readlink -f "$0")

show_usage() {
    echo "Usage: $script --appdir <path to AppDir>"
    echo
    echo "Copies python application sources to AppDir and sets the environment variable"
    echo
    echo "Variables:"
    echo "  SRC_DIR=\"/home/sai/python_sources\""
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

if [ -d "$APPDIR"/usr/app ]; then
    echo "Error: directory exists: $APPDIR/usr/app"
    exit 1
fi

mkdir -p "$APPDIR"/usr/app

echo "Copying application from sources directory $SRC_DIR to [MountedAppDir]/usr/app/"
# TODO. Make use of .gitignore in repostiory to populate exclude for rsync
rsync -aP --exclude="build_resources" --exclude="node_modules/" --exclude="build_appimage.sh" --exclude="setup.py" --exclude="dist" --exclude="*.pyc" "$SRC_DIR"/* "$APPDIR"/usr/app/
