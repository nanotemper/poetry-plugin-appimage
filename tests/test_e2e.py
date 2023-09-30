import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest


@contextmanager
def does_not_raise():
    yield


@pytest.fixture
def root_dir() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def appimage(root_dir):
    return str(
        (
            root_dir / "example_project" / "dist" / "example_project-0.1.0.42.AppImage"
        ).absolute()
    )


def test_e2e_basic(appimage: str):
    assert os.path.isfile(
        appimage
    ), "AppImage does not exist in the <src>/example_project/dist/. Run prep_for_e2e_test.sh prior"

    fname = appimage.split("/")[-1]
    assert "0.1.0.42" in fname.lstrip("example_project-").rstrip(
        ".AppImage"
    ), "Appimage does not have the expected name"


def test_e2e_versions(appimage: str):
    with does_not_raise():
        op = subprocess.check_output([appimage, "main"])
        result = json.loads(op.decode("utf8"))

    # No exception above signifies no import errors and an intact appimage

    assert "3.7" in result["python"], "expected python version to be 3.7.X"
    assert result["numpy"] == "1.18.0", "numpy version does not match"
    assert result["pyzmq"] == "22.2.1", "pyzmq version does not match"


def test_e2e_return_values(appimage: str):
    with does_not_raise():
        # a retval of 1 signifies some runtime issue with the entry point. Run the appimage manually to see what the
        # output is

        retval = subprocess.call([appimage, "retval"])
        assert retval == 255, f"Expected return value to be 255. It is {retval}"

        retval = subprocess.call([appimage, "retval --zero"])
        assert retval == 0, f"Expected return value to be 0. It is {retval}"
