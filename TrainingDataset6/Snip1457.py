def test_get_new_command(command):
    assert get_new_command(command) == 'kill 18233 && ./app'