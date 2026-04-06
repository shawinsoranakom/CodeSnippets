def test_side_effect(ssh_error):
    errormsg, path, reset, known_hosts = ssh_error
    command = Command('ssh user@host', errormsg)
    side_effect(command, None)
    expected = ['123.234.567.890 asdjkasjdakjsd\n', '111.222.333.444 qwepoiwqepoiss\n']
    assert known_hosts(path) == expected