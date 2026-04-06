def test_get_new_command(output):
    assert (get_new_command(Command('git rebase --continue', output)) ==
            'git rebase --skip')