def test_get_new_command(before, after):
    command = Command(before, output)
    assert get_new_command(command) == after