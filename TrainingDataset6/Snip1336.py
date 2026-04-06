def test_get_new_command(cmd, result):
    command = Command('heroku {}'.format(cmd), suggest_output)
    assert get_new_command(command) == result