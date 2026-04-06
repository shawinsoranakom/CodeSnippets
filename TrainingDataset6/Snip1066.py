def test_match():
    assert match(Command('cd..', 'cd..: command not found'))
    assert not match(Command('', ''))