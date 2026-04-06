def test_get_new_command(output, script, target, new_command):
    assert get_new_command(Command(script, output)) == new_command