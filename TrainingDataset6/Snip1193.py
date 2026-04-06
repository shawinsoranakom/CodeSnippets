def test_not_match(output, script):
    assert not match(Command(script, output))