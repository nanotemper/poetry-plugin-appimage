import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from cleo.helpers import option
from mako.template import Template
from poetry.console.application import Application
from poetry.console.commands.command import Command
from poetry.plugins.application_plugin import ApplicationPlugin
from poetry_plugin_export.exporter import Exporter


@dataclass
class PluginMetadata:
    app_name: str
    version: str
    categories: str
    entry_points: List
    miniconda_dist_name: str
    miniconda: str = "latest"
    python: str = ""

    def __post_init__(self):
        pass


_templates_directory = Path(__file__).parent.joinpath("templates")


@dataclass
class BuildResource:
    filename: str
    file_mode: int
    destination_dir: str
    destination_filename_pattern: Optional[str] = None
    __plugin_metadata = None

    @property
    def is_mako_template(self):
        return True if ".mako" in self.filename else False

    @property
    def destination_path(self) -> Path:
        destination_dir = Path(self.destination_dir)
        destination_dir.mkdir(exist_ok=True)
        if self.destination_filename_pattern and self.__plugin_metadata:
            destination_filename = Template(self.destination_filename_pattern).render(**vars(self.__plugin_metadata))
        else:
            destination_filename = self.filename.split(".mako")[0]

        return destination_dir.joinpath(destination_filename)

    @property
    def source_path(self):
        return _templates_directory.joinpath(self.filename).absolute()

    @property
    def template(self):
        return Template(filename=str(self.source_path))

    def add_plugin_metadata(self, plugin_metadata):
        self.__plugin_metadata = plugin_metadata


BUILD_RESOURCES = [
    BuildResource(
        "application.desktop.mako",
        0o644,
        "build_resources",
        destination_filename_pattern="${app_name}.desktop",
    ),
    BuildResource("CustomAppRun.sh.mako", 0o755, "build_resources"),
    BuildResource("build_appimage.sh.mako", 0o755, "."),
    BuildResource(
        "icon.png",
        0o755,
        "build_resources",
        destination_filename_pattern="${app_name}.png",
    ),
    BuildResource("linuxdeploy-plugin-conda.sh", 0o755, "build_resources"),
    BuildResource("linuxdeploy-plugin-compile.sh", 0o755, "build_resources"),
    BuildResource("linuxdeploy-plugin-copyapp.sh", 0o755, "build_resources"),
    BuildResource("linuxdeploy-x86_64.AppImage", 0o755, "build_resources"),
]
_FROZEN_REQUIREMENTS_FILE = "requirements_for_appimage.txt"


def cleanup(root_dir: Path):
    for build_resource in BUILD_RESOURCES:
        build_resource.destination_path.unlink()

    shutil.rmtree("build_resources")
    Path(root_dir).joinpath(_FROZEN_REQUIREMENTS_FILE).unlink()


# TODO: do not use current working dir or change to project root first
class BuildAppimageCommand(Command):
    name = "build-appimage"
    description = "Builds an AppImage for the poetry project"
    options = [
        option(
            "build-number",
            "b",
            "unique build number to identify the build (optional)",
            flag=False,
            default=None,
        ),
        option(
            "skip-cleanup",
            "sc",
            "to inspect generated build resources for the project (optional)",
            flag=True,
        ),
        option(
            "skip-build",
            "sb",
            "must be used with skip cleanup so the generated build files can be inspected and run manually (optional)",
            flag=True,
        ),
        option(
            "include-only",
            "io",
            "Specify a subfolder. only this subfolder will be included in the build (optional).",
            flag=False,
            default=None,
        ),
        option(
            "dependency-group",
            "dg",
            "dependency group to use for building the appimage (optional). defaults to poetry default requirements setting."
            "Can be used to only use specific dependencies for the appimage",
            flag=False,
            default=None,  # default has to be none, filled in the template_option function
        ),
        option(
            "entrypoints",
            "ep",
            "name(s) of the entrypoint(s) for the appimage. defaults to all entrypoints defined in pyproject.toml (optional)",
            flag=False,
            default=None,  # default has to be none, filled in the template_option function
        ),
        option(
            "exclude-gitignore",
            "eg",
            "exclude .gitignore from the appimage (optional)",
            flag=True,
        ),
    ]

    def template_option(self, option_name, options_dict, default_value):
        """
        returns the value of the option if it is set in the command line.
        If not, it returns the value from the pyproject.toml
        If there is none, it returns the default value
        """
        if self.option(option_name) is not None:
            return self.option(option_name)
        else:
            if option_name in options_dict.keys():
                return options_dict[option_name]
            return default_value

    def handle(self) -> int:
        if sys.platform != "linux":
            self.line("Please run the command from a linux environment", "error")
            return 1

        if "poetry-plugin-appimage" not in self.poetry.pyproject.data.get("tool").keys():
            self.line(
                f"Section [tool.poetry-plugin-appimage] is not defined in pyproject.toml",
                "error",
            )
            return 1

        if not self.poetry.locker.is_locked():
            self.line(
                "poetry.lock does not exist. Please create one before attempting to build appimage",
                "error",
            )
            return 1

        if not self.poetry.locker.is_fresh():
            self.line(
                "poetry.lock is not up to date with latest changes from pyproject.toml. "
                "Please run 'poetry update' before proceeding",
                "error",
            )
            return 1

        if len(list(self.poetry.pyproject.poetry_config["scripts"].keys())) == 0:
            self.line("No entry points defined in section [tools.poetry.scripts]", "warning")
        options_dict = dict(self.poetry.pyproject.data.get("tool")["poetry-plugin-appimage"])
        self.line(f" pre parsing: {options_dict}")
        options_dict["include-only"] = self.template_option("include-only", options_dict, None)
        options_dict["dependency-group"] = self.template_option("dependency-group", options_dict, None)
        options_dict["entrypoints"] = self.template_option("entrypoints", options_dict, None)
        options_dict["exclude-gitignore"] = self.template_option("exclude-gitignore", options_dict, False)
        options_dict["skip-cleanup"] = self.template_option("skip-cleanup", options_dict, False)
        options_dict["skip-build"] = self.template_option("skip-build", options_dict, False)

        self.line(f"running with the following options: {options_dict}")
        self.line("checking for entrypoints")
        entry_points = []
        allowed_entrypoints = []
        if options_dict["entrypoints"] is not None:
            allowed_entrypoints += options_dict["entrypoints"].strip(" ").strip("[").strip("]").split(",")

        for entry_point_name, entry_point_def in self.poetry.pyproject.poetry_config["scripts"].items():
            if len(allowed_entrypoints) > 0 and entry_point_name not in allowed_entrypoints:
                self.line(f"Skipping entrypoint: {entry_point_name} because it is not in allowed entrypoints setting")
                continue
            module_name, function_def = entry_point_def.split(":")
            cmd = f'-c "import {module_name}; {module_name}.{function_def}()"'
            entry_points.append((entry_point_name, cmd))
            self.line(f"Added entrypoint: {entry_point_name}")

        build_number: Optional[int] = self.option("build-number")
        version: str = self.poetry.local_config.get("version")
        app_name: str = self.poetry.local_config.get("name")

        if build_number is not None:
            self.line(f"Build Number: {build_number}", "comment")
            version = f"{version}.{build_number}"
        self.line(f"Starting build for {app_name}. Version: #{version}", "comment")

        # get correct miniconda distribution name from pyproject.toml
        if platform.processor() == "x86_64":
            target_platform_string = "x86_64"
        elif platform.processor() == "i386":
            target_platform_string = "x86"
        else:
            raise SystemError("Currently only supports x86 and amd64 architectures")

        python_version_string = f"py{options_dict['python'].replace('.', '')}_" if "python" in options_dict else ""
        miniconda_version_string = options_dict["miniconda"] if "miniconda" in options_dict else "latest"
        miniconda_dist_name = (
            f"Miniconda3-{python_version_string}{miniconda_version_string}-Linux-{target_platform_string}.sh"
        )
        self.line("writing metadata")
        metadata = PluginMetadata(
            **{
                **{
                    "app_name": app_name,
                    "version": version,
                    "categories": options_dict["categories"],
                    "miniconda": options_dict["miniconda"],
                    "python": options_dict["python"],
                    "entry_points": entry_points,
                    "miniconda_dist_name": miniconda_dist_name,
                },
            }
        )
        # directory that contains the pyproject.toml file
        root_dir = self.poetry.file.path.parent

        e = Exporter(self.poetry, self.io)
        self.line("checking for dependency groups")
        if options_dict["dependency-group"] is not None:
            self.line(f"only using the specified dependency group {options_dict['dependency-group']}")
            e = e.only_groups([options_dict["dependency-group"]])

        e.export(
            "requirements.txt",
            root_dir,
            _FROZEN_REQUIREMENTS_FILE,
        )
        self.line(
            f"Generated requirements file for this project at <ROOT>/requirements_for_appimage.txt",
            "comment",
        )

        for build_resource in BUILD_RESOURCES:
            build_resource.add_plugin_metadata(metadata)

            if build_resource.is_mako_template:
                with build_resource.destination_path.open("w", newline="\n") as f:
                    f.write(build_resource.template.render(**vars(metadata)))
            else:
                shutil.copy(build_resource.source_path, build_resource.destination_path)

            build_resource.destination_path.chmod(build_resource.file_mode)

        return_value = 0
        if not options_dict["skip-build"]:
            command = ["./build_appimage.sh", metadata.version]
            if options_dict["include-only"] is not None:
                command += ["--include-only", options_dict["include-only"]]
            if options_dict["exclude-gitignore"]:
                command += ["--exclude-gitignore"]

            try:
                return_value = subprocess.call(command)
                if return_value != 0:
                    self.line(
                        "Return value from build script is non-zero. Please check the logs",
                        "error",
                    )
            except Exception as e:
                self.line(
                    f"Exception occurred executing the build. Details: {repr(e)}",
                    "error",
                )
                return_value = 1

        if not options_dict["skip-cleanup"]:
            self.line("Cleaning up generated build resources", "comment")
            cleanup(root_dir)

        return return_value


class PoetryAppimagePlugin(ApplicationPlugin):
    def activate(self, application: Application):
        application.command_loader.register_factory("build-appimage", lambda: BuildAppimageCommand())
