import subprocess

import pytest

from poetry_plugin_appimage.plugin import BUILD_RESOURCES, PluginMetadata


@pytest.fixture
def metadata():
    return PluginMetadata(
        app_name="appname with spaces",
        version="4.2.0",
        miniconda="0.2.4",
        miniconda_dist_name="Miniconda3-py37_0.2.4-Linux-x86_64.sh",
        python="3.7",
        categories="ConsoleOnly;",
        entry_points=[],
    )


@pytest.mark.parametrize(
    "mako_resource",
    [resource for resource in BUILD_RESOURCES if resource.is_mako_template],
)
def test_mako_resource(mako_resource, monkeypatch, tmp_path, metadata):
    monkeypatch.setattr(mako_resource, "destination_dir", tmp_path.absolute())
    with mako_resource.destination_path.open("w", newline="\n") as f:
        f.write(mako_resource.template.render(**vars(metadata)))

    if ".sh" in str(mako_resource.destination_path.absolute()):
        subprocess.call([f"shellcheck", str(mako_resource.destination_path.absolute())])
