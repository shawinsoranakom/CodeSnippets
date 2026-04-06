def test_get_new_command(command, url):
    assert get_new_command(command) == open_command(url)