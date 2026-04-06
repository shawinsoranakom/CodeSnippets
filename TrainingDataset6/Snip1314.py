def exists(mocker):
    return mocker.patch('thefuck.rules.gradle_wrapper.os.path.isfile',
                        return_value=True)