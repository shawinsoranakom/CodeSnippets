def test_get_new_command(script, new_cmd, pip_unknown_cmd):
    assert get_new_command(Command(script,
                                   pip_unknown_cmd)) == new_cmd