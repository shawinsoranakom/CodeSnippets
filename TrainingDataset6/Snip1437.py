def test_get_new_command_mocked(subp_mock, command, fixed):
    subp_mock.check_output.return_value = PKGFILE_OUTPUT_LLC
    assert get_new_command(command) == fixed