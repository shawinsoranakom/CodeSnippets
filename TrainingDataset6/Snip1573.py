def isfile(mocker):
    return mocker.patch('os.path.isfile', return_value=True)