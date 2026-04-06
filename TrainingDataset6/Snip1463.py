def test_get_new_command():
    assert (get_new_command(Command('./test_sudo.py', ''))
            == 'python ./test_sudo.py')