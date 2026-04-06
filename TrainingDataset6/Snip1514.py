def test_get_new_command(command, new_command):
    assert switch_lang.get_new_command(command) == new_command