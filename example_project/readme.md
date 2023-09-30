## Example Project

With `poetry` and `poetry-plugin-appimage` installed on your system, navigate to this sub-directory and run `poetry build-appimage`. The AppImage is created is at `dist/example_project.AppImage`

You may now execute the AppImage and invoke the two entry points that have been automatically created.

`./example_project.AppImage main`
`./example_project.AppImage retval`

These entrypoints have been sourced from `[tool.poetry.scripts]` defined in `pyproject.toml`. 

This example project also serves as a test fixture, check tests/test_e2e.py
