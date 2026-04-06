def bins(self, mocker):
        callables = list()
        for name in ['diff', 'ls', 'café']:
            bin_mock = mocker.Mock(name=name)
            bin_mock.configure_mock(name=name, is_dir=lambda: False)
            callables.append(bin_mock)
        path_mock = mocker.Mock(iterdir=mocker.Mock(return_value=callables))
        return mocker.patch('thefuck.utils.Path', return_value=path_mock)