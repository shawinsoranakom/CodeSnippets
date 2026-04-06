def isdir(mocker):
    return mocker.patch('thefuck.rules.prove_recursively'
                        '.os.path.isdir')