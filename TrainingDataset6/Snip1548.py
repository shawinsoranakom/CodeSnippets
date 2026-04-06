def envs(mocker):
    return mocker.patch(
        'thefuck.rules.workon_doesnt_exists._get_all_environments',
        return_value=['thefuck', 'code_view'])