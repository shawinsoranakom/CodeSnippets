def test_match():
    assert match(Command('ls', ''))
    assert not match(Command('ls', 'file.py\n'))