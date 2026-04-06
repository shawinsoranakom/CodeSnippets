def test_match(get_actual_scm_mock, script, output, actual_scm):
    get_actual_scm_mock.return_value = actual_scm
    assert match(Command(script, output))