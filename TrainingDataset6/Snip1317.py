def test_get_new_command(script, result):
    command = Command(script, '')
    assert get_new_command(command) == result