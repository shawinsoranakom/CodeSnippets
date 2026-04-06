def test_not_match(script, output):
    assert not match(Command(script, output=output))