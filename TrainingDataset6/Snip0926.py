def test_print_alias(mocker):
    settings_mock = mocker.patch('thefuck.entrypoints.alias.settings')
    _get_alias_mock = mocker.patch('thefuck.entrypoints.alias._get_alias')
    known_args = Mock()
    print_alias(known_args)
    settings_mock.init.assert_called_once_with(known_args)
    _get_alias_mock.assert_called_once_with(known_args)