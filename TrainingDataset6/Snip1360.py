def file_exists(mocker):
    return mocker.patch('os.path.exists', return_value=True)