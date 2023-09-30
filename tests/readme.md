## Tests

- `test_mako_template` is for static testing of shell scripts generated using mako templates. It uses `shellchecker` tool
- `test_e2e` is end to end testing of the build toolchain
  - First execute `./tests/prep_for_e2e_test.sh` to create a AppImage from the example project and then execute e2e test
