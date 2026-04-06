def test_match():
    command = Command('brew install thefuck', output)
    assert match(command)