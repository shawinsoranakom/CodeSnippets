def test_match_mocked(subp_mock, command, return_value):
    subp_mock.check_output.return_value = return_value
    assert match(command)