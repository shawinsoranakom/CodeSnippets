def get_actual_scm_mock(mocker):
    return mocker.patch('thefuck.rules.scm_correction._get_actual_scm',
                        return_value=None)