def test_get_new_command(output):
    assert (get_new_command(Command('git pull', output))
            == "git stash && git pull && git stash pop")