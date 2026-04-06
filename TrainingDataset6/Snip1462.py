def test_match():
    assert match(Command('temp.py', 'Permission denied'))
    assert not match(Command('', ''))