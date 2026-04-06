def test_match():
    command = Command('brew install sshfs', output)
    assert match(command)