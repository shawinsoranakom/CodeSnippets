def test_match(script, output):
    assert match(Command(script, output))