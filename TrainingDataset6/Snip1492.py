def test_not_match(get_actual_scm_mock, script, output, actual_scm):
    get_actual_scm_mock.return_value = actual_scm
    assert not match(Command(script, output))