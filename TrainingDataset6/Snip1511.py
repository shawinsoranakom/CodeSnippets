def test_get_new_command(script, output, result):
    assert get_new_command(Command(script, output)) == result