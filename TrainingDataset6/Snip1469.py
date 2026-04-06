def test_get_new_command(
    script, filename, module_name, corrected_script, module_error_output
):
    assert get_new_command(Command(script, module_error_output)) == corrected_script