def test_get_new_command():
    assert get_new_command(Command('ls empty_dir', '')) == 'ls -A empty_dir'
    assert get_new_command(Command('ls', '')) == 'ls -A'