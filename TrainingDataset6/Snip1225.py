def test_get_new_command(script, branch_name, new_command, output):
    assert get_new_command(Command(script, output)) == new_command