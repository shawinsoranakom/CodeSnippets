def test_get_new_command():
    new_command = get_new_command(Command('git push', error_msg('foo', 'bar')))
    assert new_command == 'git push origin HEAD:bar'