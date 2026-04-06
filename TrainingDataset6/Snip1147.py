def path_exists(mocker):
    return mocker.patch('thefuck.rules.git_add.Path.exists',
                        return_value=True)