def test_get_new_command(output):
    assert (get_new_command(Command('git pull', output))
            == "git branch --set-upstream-to=origin/master master && git pull")