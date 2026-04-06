def test_get_new_command(script, output, new_command):
    assert get_new_command(Command(script, output)) == new_command