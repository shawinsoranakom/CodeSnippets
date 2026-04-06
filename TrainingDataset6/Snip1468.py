def test_match(script, filename, module_name, corrected_script, module_error_output):
    assert match(Command(script, module_error_output))