import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest


@contextmanager
def does_not_raise():
    yield


@pytest.fixture(scope="session")
def root_dir() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def appimage_for_tests(root_dir):
    subprocess.run(str(root_dir / "tests" / "prep_for_e2e_test.sh"), cwd=root_dir, shell=True, check=True)
    yield str((root_dir / "example_project" / "dist" / "example_project-0.1.0.42.AppImage").absolute())
    os.remove(str((root_dir / "example_project" / "dist" / "example_project-0.1.0.42.AppImage").absolute()))


def test_e2e_basic(appimage_for_tests):
    assert os.path.isfile(appimage_for_tests), "AppImage from appimage_for_tests fixture did not build correctly"

    fname = appimage_for_tests.split("/")[-1]
    assert "0.1.0.42" in fname.lstrip("example_project-").rstrip(
        ".AppImage"
    ), "Appimage does not have the expected name"


def test_e2e_versions(appimage_for_tests):
    with does_not_raise():
        op = subprocess.check_output([appimage_for_tests, "main"])
        result_string = "".join(op.decode("utf8").replace("\n", "").partition("{")[1:])
        result = json.loads(result_string)

    # No exception above signifies no import errors and an intact appimage

    assert "3.7" in result["python"], "expected python version to be 3.7.X"
    assert result["numpy"] == "1.18.0", "numpy version does not match"
    assert result["pyzmq"] == "22.2.1", "pyzmq version does not match"


def test_e2e_return_values(appimage_for_tests):
    with does_not_raise():
        # a retval of 1 signifies some runtime issue with the entry point. Run the appimage manually to see what the
        # output is

        retval = subprocess.call([appimage_for_tests, "retval"])
        assert retval == 255, f"Expected return value to be 255. It is {retval}"

        retval = subprocess.call([appimage_for_tests, "retval --zero"])
        assert retval == 0, f"Expected return value to be 0. It is {retval}"


def test_e2e_dependency_groups(root_dir, appimage_for_tests):
    """
    Tests that we only include the main dependency group
    """
    subprocess.run([appimage_for_tests, "--appimage-extract"])
    site_packages = os.listdir(root_dir / "squashfs-root" / "usr" / "conda" / "lib" / "python3.7" / "site-packages")

    # black and isort are defined in "dev" dependency group of the example project
    # and should not be packed into the appimage
    assert not any("black" in package_name for package_name in site_packages)
    assert not any("isort" in package_name for package_name in site_packages)

    assert any("numpy" in package_name for package_name in site_packages)
    assert any("zmq" in package_name for package_name in site_packages)

    shutil.rmtree(root_dir / "squashfs-root")
