def test_get_new_command(branches, command, new_command, git_branch):
    git_branch(branches)
    assert get_new_command(command) == new_command