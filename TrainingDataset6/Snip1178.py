def test_not_match():
    assert not match(Command('', ''))
    assert not match(Command('git commit', ''))
    assert not match(Command('git branch', ''))
    assert not match(Command('git stash list', ''))