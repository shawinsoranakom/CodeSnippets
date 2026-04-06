def test_get_new_command(output):
    assert (get_new_command(Command('git add dist/*.js', output))
            == "git add --force dist/*.js")