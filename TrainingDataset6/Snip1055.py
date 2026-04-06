def isdir(mocker):
    return mocker.patch('thefuck.rules.cat_dir'
                        '.os.path.isdir')