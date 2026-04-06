def config_exists(mocker):
    path_mock = mocker.patch('thefuck.shells.generic.Path')
    return path_mock.return_value \
        .expanduser.return_value \
        .exists