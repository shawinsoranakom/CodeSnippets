def test_get_new_command():
    new_command = get_new_command(Command('apt-get search foo', ''))
    assert new_command == 'apt-cache search foo'