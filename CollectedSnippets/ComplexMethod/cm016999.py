def test_match(ssh_error):
    errormsg, _, _, _ = ssh_error
    assert match(Command('ssh', errormsg))
    assert match(Command('ssh', errormsg))
    assert match(Command('scp something something', errormsg))
    assert match(Command('scp something something', errormsg))
    assert not match(Command(errormsg, ''))
    assert not match(Command('notssh', errormsg))
    assert not match(Command('ssh', ''))