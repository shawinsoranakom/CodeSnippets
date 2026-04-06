def get_aliases(mocker):
    mocker.patch('thefuck.shells.shell.get_aliases',
                 return_value=['vim', 'apt-get', 'fsck', 'fuck'])