def test_get_new_command(output, script, new_cmd):
    new_cmd = ['git bisect %s' % cmd for cmd in new_cmd]
    assert get_new_command(Command(script, output)) == new_cmd