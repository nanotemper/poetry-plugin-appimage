## poetry-plugin-appimage

A plugin for [poetry](https://github.com/python-poetry/poetry) packaging and dependency manager that introduces a new command to build an [AppImage](https://appimage.org/) for a python project.

### Installation

 * Make sure you are using `poetry>=1.2.0`
 * Install the plugin to your poetry installation (aka poetry self) by running the command `poetry self add poetry-plugin-appimage`
 * Run `poetry self show plugins` to list all plugins installed by poetry. This command should display `poetry-plugin-appimage` and `poetry-plugin-export`

### Usage

`poetry build-appimage --help`
~~~
Description:
  Builds an AppImage for the poetry project

Usage:
  build-appimage [options]

Options:
  -b, --build-number=BUILD-NUMBER  unique build number to identify the build (optional)
  -sc, --skip-cleanup              to inspect generated build resources for the project (optional)
  -sb, --skip-build                must be used with skip cleanup so the generated build files can be inspected and run manually (optional)
  -io, --include-only=INCLUDE-ONLY          specify a subfolder. only this subfolder will be included in the build (optional).
  -dg, --dependency-group=DEPENDENCY-GROUP  dependency group to use for building the appimage (optional). defaults to poetry default requirements setting.Can be used to only use specific dependencies for the appimage
  -ep, --entrypoints=ENTRYPOINTS            name(s) of the entrypoint(s) for the appimage. defaults to all entrypoints defined in pyproject.toml (optional)
~~~

Define the following section in your project's `pyproject.toml` with a valid [miniconda version](https://repo.anaconda.com/miniconda/) and python version. 
If python and miniconda are defined, the corresponding distribution
of Miniconda3-py\<**python**\>-\<**miniconda**\> will be used.
If either is not defined, Miniconda3-latest will be used.


Categories must be seperated by a semi-colon.

~~~
[tool.poetry-plugin-appimage]
miniconda = "4.8.3"
python = "3.7"
categories = "ConsoleOnly;"
~~~

Start a build using `poetry build-appimage -b 42` where 42 is build identification number. The resultant binary is 
stored at `dist/<APP_NAME>-<VERSION>.<BUILD_NUMBER>.AppImage`

### Example/Sample Project

Refer `<src>/example_project` for an ex*s*ample project.

### How does it work ?

This plugin only runs on a suitable Linux machine, it depends on the new plugin system introduced in poetry 1.2.0 (hard requirement). It uses `poetry.lock` file as frozen dependencies for the python distribution within the AppImage and the content from `pyproject.toml` as metadata required for building the AppImage. Furthermore, it uses scripts defined in `pyproject.toml` as entry points of the AppImage.

This plugin is a wrapper that uses [linuxdeploy](https://github.com/linuxdeploy) toolchain and [linuxdeploy-plugin-conda](linuxdeploy-plugin-conda) to create AppImages.
