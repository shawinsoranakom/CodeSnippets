def test_get_new_command(script, result):
    command = Command(script, output)
    assert get_new_command(command) == result