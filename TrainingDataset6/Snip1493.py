def test_get_new_command(get_actual_scm_mock, script, actual_scm, result):
    get_actual_scm_mock.return_value = actual_scm
    new_command = get_new_command(Command(script, ''))
    assert new_command == result