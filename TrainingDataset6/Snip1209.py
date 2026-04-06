def test_get_new_command(wrong, fixed):
    assert get_new_command(Command(wrong, git_stash_err)) == fixed