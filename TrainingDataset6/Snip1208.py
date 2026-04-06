def test_not_match():
    assert not match(Command("git", git_stash_err))