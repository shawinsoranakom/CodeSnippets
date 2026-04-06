def test_match(git_not_command, git_command, git_not_command_one_of_this):
    assert match(Command('git brnch', git_not_command))
    assert match(Command('git st', git_not_command_one_of_this))
    assert not match(Command('ls brnch', git_not_command))
    assert not match(Command('git branch', git_command))