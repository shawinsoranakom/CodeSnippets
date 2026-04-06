def test_get_new_command():
    assert get_new_command(Command('ls file.py', '')) == 'ls -lah file.py'
    assert get_new_command(Command('ls', '')) == 'ls -lah'