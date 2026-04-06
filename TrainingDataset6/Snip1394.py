def test_get_new_command(mocker, command, new_command):
    assert get_new_command(command) == new_command