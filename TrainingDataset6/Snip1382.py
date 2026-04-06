def test_get_new_command(script, result):
    assert get_new_command(Command(script, '')) == result