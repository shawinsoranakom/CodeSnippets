def test_match():
    assert match(Command('sl', ''))
    assert not match(Command('ls', ''))