def test_get_new_command(output, script, branch_name, new_command):
    assert get_new_command(Command(script, output)) == new_command