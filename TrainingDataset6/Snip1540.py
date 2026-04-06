def test_not_match():
    assert not match(Command('', ''))
    assert not match(Command('sudo ls', 'Permission denied'))
    assert not match(Command('ls', 'you cannot perform this operation as root'))