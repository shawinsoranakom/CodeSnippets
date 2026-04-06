def test_match(output):
    assert match(Command('sudo ls', output))