def test_get_new_command(output, new_command, script, src_branch_name, branch_name):
    assert get_new_command(Command(script, output)) == new_command