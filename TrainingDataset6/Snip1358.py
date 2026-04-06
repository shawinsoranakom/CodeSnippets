def test_not_match(script, output):
    command = Command(script, output)
    assert not match(command)