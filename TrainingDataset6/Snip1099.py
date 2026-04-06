def test_get_new_command(zip_error, script, fixed, filename):
    zip_error(filename)
    assert get_new_command(Command(script, '')) == fixed