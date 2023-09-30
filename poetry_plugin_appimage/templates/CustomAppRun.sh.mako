#!/bin/sh

# NOTE: Make sure only `sh` specification is used. Using super-sets like `bash` won't work well with AppImage
#  because, AppImage is created to work on large number of platforms, sh provides greater portability

if [ -z "$APPDIR" ]; then
APPDIR=$(readlink -f "$(dirname "$0")");
fi

# To address unknown symbol error deflateInit2_ when libTML_lib.so is loaded. This symbol is part of libz
# although libz is present on every host system, it is not loaded by default and causes runtime issues
export LD_PRELOAD=/lib/x86_64-linux-gnu/libz.so.1

# This adds copied application (by linuxdeploy-plugin-copyapp) to PYTHONPATH
export PYTHONPATH="$APPDIR"/usr/app

# For debugging purposes. A python interpreter with all packages specified in requirements.txt
if [ "$1" = "interpreter" ]; then
exec "$APPDIR"/usr/bin/python
fi

% for entry_point_name, cmd in entry_points:
if [ "$1" = "${entry_point_name}" ]; then
shift
exec "$APPDIR"/usr/bin/python ${cmd} "$@"
fi

%endfor
