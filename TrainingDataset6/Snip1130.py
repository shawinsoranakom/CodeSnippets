def test_get_new_management_command_subcommand(wrong, fixed, output):
    command = Command('docker {}'.format(wrong), output)
    assert get_new_command(command) == ['docker {}'.format(x) for x in fixed]