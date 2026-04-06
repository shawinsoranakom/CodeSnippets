def test_get_new_command(command, new_command, mocker):
    assert get_new_command(command) == new_command