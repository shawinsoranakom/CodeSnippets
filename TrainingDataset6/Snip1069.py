def file_access(mocker):
    return mocker.patch('os.access', return_value=False)