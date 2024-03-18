#!/bin/bash

set -e

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd > /dev/null
}


if [ "$1" == "--help" ]; then
  echo -e "Usage: $(basename "$0") BUILD_NUMBER [--local-packages] [--include-only PATH] [--exclude-gitignore] \n\n"
  echo -e "FULL_BUILD_NUMBER\t\trequired argument"
  echo -e "--local-packages\toptional argument"
  echo -e "--include-only PATH\toptional argument"
  echo -e "--exclude-gitignore\toptional argument"
    exit 0
fi

# This script expects a command line argument with full build number (aka version identifier)
if [[ -z $1 ]]; then
    echo "FULL_BUILD_NUMBER must be supplied"
    exit 1
fi

# unset LINUXDEPLOY_INCLUDE_ONLY if previously set
if [[ -n $LINUXDEPLOY_INCLUDE_ONLY ]]; then
    unset LINUXDEPLOY_INCLUDE_ONLY
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --local-packages)
            export LOCAL_PACKAGES="True"
            shift
            ;;
        --include-only)
            INCLUDE_ONLY_PATH=$2
            export LINUXDEPLOY_INCLUDE_ONLY=$INCLUDE_ONLY_PATH
            shift 2
            ;;
        --exclude-gitignore)
            export LINUXDEPLOY_EXCLUDE_GITIGNORE="True"
            shift
            ;;
        *)
            FULL_BUILD_NUMBER=$1
            shift
            ;;
    esac
done

# Set default value for LINUXDEPLOY_EXCLUDE_GITIGNORE if not provided
if [[ -z $LINUXDEPLOY_EXCLUDE_GITIGNORE ]]; then
    export LINUXDEPLOY_EXCLUDE_GITIGNORE="False"
fi

# Absolute path of application sources
REPO_ROOT=$(readlink -f "$(dirname "$(dirname "$0")")")

# AppImage is saved in dist folder of repository
mkdir -p dist

# Temporary build directory where AppDir is created before squashing it into AppImage
BUILD_DIR=$(mktemp -d -p /tmp ${app_name}-build-XXXXXX)
pushd "$BUILD_DIR"/

# Handle cleanup of temporary build directory
cleanup() {
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
        rm -rf "$REPO_ROOT/build_resources/.local_packages"
    fi
}
#trap cleanup EXIT

# Env for linuxdeploy and linuxdeploy-plugin-conda
export ARCH="x86_64"

# Env for linuxdeploy-plugin-conda
export MINICONDA_DIST="${miniconda_dist_name}"
export PIP_REQUIREMENTS="-r requirements_for_appimage.txt"  # install argument is added by linuxdeploy-plugin-conda.sh
export PIP_WORKDIR="$REPO_ROOT"
export CONDA_SKIP_CLEANUP="strip;.a;cmake;doc;man;"

# Env for linuxdeploy-plugin-copyapp
export SRC_DIR="$REPO_ROOT"
export BUILD_COUNTER_FOR_IMAGE="$BUILD_COUNTER"

# Copy linuxdeploy binary and plugins
cp "$REPO_ROOT"/build_resources/linuxdeploy* "$BUILD_DIR"

if [[ "$LOCAL_PACKAGES" == "True" ]]; then
  mkdir -p "$REPO_ROOT"/build_resources/.local_packages
  finished=false
  while ! $finished; do
    read -r -p "(Press enter to skip input) Supply path to a package: " path
    if test -z "$path"; then
        finished=true
    else
        pushd "$path"
        python3 setup.py -q sdist --dist-dir "$REPO_ROOT"/build_resources/.local_packages
        popd
    fi
  done
  LOCAL_PACKAGES=$(find "$REPO_ROOT/build_resources/.local_packages" -type f)
  export PIP_REQUIREMENTS="$PIP_REQUIREMENTS $LOCAL_PACKAGES"
fi

./linuxdeploy-x86_64.AppImage --appdir AppDir --plugin copyapp --plugin conda --plugin compile -e "$(which readelf)" -i "$REPO_ROOT"/build_resources/${app_name}.png -d "$REPO_ROOT"/build_resources/${app_name}.desktop --output appimage --custom-apprun "$REPO_ROOT"/build_resources/CustomAppRun.sh

# Rename the AppImage appropriately, there is only going to be one file
mv ${app_name}*.AppImage ${app_name}-"$FULL_BUILD_NUMBER".AppImage
mv ${app_name}* "$REPO_ROOT"/dist/
