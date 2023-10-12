#!/bin/bash

if ! command -v poetry &> /dev/null; then
  echo "Cannot find poetry binary"
  exit 1
fi

if [[ -n $POETRY_ACTIVE ]]; then
  echo "A poetry environment is already active. Deactivate it first"
  exit 2
fi

REPO_ROOT="$(dirname "$(dirname "$(readlink -fm "$0")")")"

pushd "$REPO_ROOT/example_project/" || exit
rm -f dist/*.AppImage
poetry install
poetry run poetry build-appimage -b 42
poetry env remove "$(poetry env list | awk '{print $1;}')"
popd || exit
