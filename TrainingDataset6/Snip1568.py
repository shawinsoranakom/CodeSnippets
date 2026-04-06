def test_not_match(command, output):
    assert not match(Command(command, output))