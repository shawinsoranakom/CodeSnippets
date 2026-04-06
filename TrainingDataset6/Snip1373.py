def test_match():
    assert match(Command('mandiff', 'mandiff: command not found'))
    assert not match(Command('', ''))