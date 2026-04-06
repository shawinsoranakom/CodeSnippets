def test_get_new_command():
    assert get_new_command(Command('cs /etc/', 'cs: command not found')) == 'cd /etc/'