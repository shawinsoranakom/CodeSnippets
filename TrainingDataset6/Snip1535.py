def test_get_new_command(command, new_commands):
    assert get_new_command(command) == new_commands