def test_get_new_command(command, result):
    assert get_new_command(command)[0] == result