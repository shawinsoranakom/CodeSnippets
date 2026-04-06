def test_get_new_command(output, script, result):
    assert get_new_command(Command(script, output)) == result