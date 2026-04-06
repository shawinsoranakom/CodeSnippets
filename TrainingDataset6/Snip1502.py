def test_get_new_command(ssh_error, monkeypatch):
    errormsg, _, _, _ = ssh_error
    assert get_new_command(Command('ssh user@host', errormsg)) == 'ssh user@host'