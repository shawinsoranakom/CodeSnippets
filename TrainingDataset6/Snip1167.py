def test_get_new_command(output):
    assert get_new_command(Command('git branch -d branch', output))\
        == "git branch -D branch"