def test_match(output):
    assert match(Command('git branch -d branch', output))
    assert not match(Command('git branch -d branch', ''))
    assert not match(Command('ls', output))