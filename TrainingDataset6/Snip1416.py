def test_match(script, pyenv_cmd, output):
    assert match(Command(script, output=output))