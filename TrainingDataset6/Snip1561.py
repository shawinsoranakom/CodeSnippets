def test_get_new_command(command, result):
    fixed_command = get_new_command(command)
    if isinstance(fixed_command, list):
        fixed_command = fixed_command[0]

    assert fixed_command == result