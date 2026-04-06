def test_get_new_command(script, output, result):
    command = Command(script, output)

    assert get_new_command(command)[0] == result