def test_get_new_command(command, new_command):
    isdir.return_value = True
    assert get_new_command(command) == new_command