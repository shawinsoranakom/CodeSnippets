def test_get_new_command(output):
    assert (get_new_command(Command('git stash pop', output))
            == "git add --update && git stash pop && git reset .")