def test_match(wrong):
    assert match(Command(wrong, git_stash_err))