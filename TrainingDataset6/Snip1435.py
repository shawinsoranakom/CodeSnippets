def test_match_mocked(subp_mock, command):
    subp_mock.check_output.return_value = PKGFILE_OUTPUT_LLC
    assert match(command)