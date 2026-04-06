def test_get_new_command(script, new_cmd, output):
    assert get_new_command((Command(script, output))) == new_cmd