def test_match():
    command = Command('brew update thefuck', output)
    assert match(command)