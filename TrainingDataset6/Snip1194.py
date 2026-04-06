def test_get_new_command(script, new_command):
    assert get_new_command(Command(script, "")) == new_command