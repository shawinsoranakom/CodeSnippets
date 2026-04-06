def test_get_new_command(script, output, result):
    new_command = get_new_command(Command(script, output))
    assert new_command[0] == result