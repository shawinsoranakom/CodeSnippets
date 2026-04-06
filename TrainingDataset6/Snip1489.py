def test_get_new_command():
    assert (get_new_command(Command('rm -rf /', ''))
            == 'rm -rf / --no-preserve-root')