def shell_pid(mocker):
    return mocker.patch('thefuck.entrypoints.not_configured._get_shell_pid',
                        new_callable=MagicMock)