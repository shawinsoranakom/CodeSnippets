def test_get_new_command_not_valid_object(script, output_not_valid_object, new_command):
    assert get_new_command(Command(script, output_not_valid_object)) == new_command