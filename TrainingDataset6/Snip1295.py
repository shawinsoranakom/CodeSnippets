def test_match(output):
    assert match(Command('git stash pop', output))
    assert not match(Command('git stash', ''))