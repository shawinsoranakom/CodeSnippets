def test_get_new_command_branch_exists(script, output_branch_exists, new_command):
    assert get_new_command(Command(script, output_branch_exists)) == new_command