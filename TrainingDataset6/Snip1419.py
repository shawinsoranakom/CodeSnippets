def test_get_new_command(script, pyenv_cmd, output, result):
    assert result in get_new_command(Command(script, output))