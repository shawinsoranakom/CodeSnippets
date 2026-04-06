def test_get_new_command(before, after):
    assert get_new_command(Command(before, '')) == after