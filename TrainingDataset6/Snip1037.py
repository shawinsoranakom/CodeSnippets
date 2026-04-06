def test_get_new_command(output, new_command, script, formula):
    assert get_new_command(Command(script, output)) == new_command