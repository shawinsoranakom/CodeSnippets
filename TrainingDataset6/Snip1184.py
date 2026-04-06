def test_get_branches(branches, branch_list, git_branch):
    git_branch(branches)
    assert list(get_branches()) == branch_list