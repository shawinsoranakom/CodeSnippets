def test_match(output):
    assert match(Command('grep -h', output))