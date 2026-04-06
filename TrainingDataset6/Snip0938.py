def logs(mocker):
    return mocker.patch('thefuck.entrypoints.not_configured.logs',
                        new_callable=MagicMock)