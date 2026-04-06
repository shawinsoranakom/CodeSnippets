def path_exists(mocker):
    path_mock = mocker.patch('thefuck.rules.path_from_history.Path')
    exists_mock = path_mock.return_value.expanduser.return_value.exists
    exists_mock.return_value = True
    return exists_mock