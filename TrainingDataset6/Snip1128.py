def test_get_new_command(wrong, fixed):
    command = Command('docker {}'.format(wrong), output(wrong))
    assert get_new_command(command) == ['docker {}'.format(x) for x in fixed]