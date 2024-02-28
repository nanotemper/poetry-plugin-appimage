#! /bin/bash

# One solution to deploy application sources to the AppDir. It follows linuxdeploy spec (version 1)

set -e

script=$(readlink -f "$0")

show_usage() {
    echo "Usage: $script --appdir <path to AppDir>"
    echo
    echo "Copies python application sources to AppDir and sets the environment variable"
    echo "Uses an optional environment variable LINUXDEPLOY_INCLUDE_ONLY to specify which files/folders to include"
    echo "This is because linuxdeploy does not let me pass extra arguments."
}

APPDIR=
LINUXDEPLOY_INCLUDE_ONLY="$LINUXDEPLOY_INCLUDE_ONLY"

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
# TODO. Make use of .gitignore in repository to populate exclude for rsync

if [ -z "$LINUXDEPLOY_INCLUDE_ONLY" ]; then
    rsync -aP --exclude="build_resources" --exclude="node_modules/" --exclude="build_appimage.sh" --exclude="setup.py" --exclude="dist" --exclude="*.pyc" "$SRC_DIR"/* "$APPDIR"/usr/app/ 
else
    echo "running with include only: $LINUXDEPLOY_INCLUDE_ONLY"
    pushd $SRC_DIR
    find "." -path "*$LINUXDEPLOY_INCLUDE_ONLY*" -not -path "*.tox*" -not -path "$SRC_DIR/dist/*" -not -name "*.pyc" -not -path "*__pycache__*"  > files_list.txt
    cat files_list.txt | cut -c 3- > modified_files_list.txt
    cat modified_files_list.txt
    popd
    rsync -aP --files-from="$SRC_DIR/modified_files_list.txt" --exclude="build_resources" --exclude="node_modules/" --exclude="build_appimage.sh" --exclude="setup.py" --exclude="dist" --exclude="*.pyc" "$SRC_DIR"/ "$APPDIR"/usr/app/
    rm "$SRC_DIR/modified_files_list.txt" "$SRC_DIR/files_list.txt"
fi

