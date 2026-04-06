def test_get_new_command():
    assert get_new_command(Command('git clone git clone foo', output_clean)) == 'git clone foo'