def test_match(script):
    command = Command(script, output)
    assert match(command)