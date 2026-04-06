def test_get_new_command(script):
    assert get_new_command(Command(script, '')) == 'git reset HEAD~'