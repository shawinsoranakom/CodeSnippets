def test_get_new_command(git_not_command, git_not_command_one_of_this,
                         git_not_command_closest):
    assert (get_new_command(Command('git brnch', git_not_command))
            == ['git branch'])
    assert (get_new_command(Command('git st', git_not_command_one_of_this))
            == ['git stats', 'git stash', 'git stage'])
    assert (get_new_command(Command('git tags', git_not_command_closest))
            == ['git tag', 'git stage'])