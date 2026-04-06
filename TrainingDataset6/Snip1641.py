def Popen(self, mocker):
        mock = mocker.patch('thefuck.shells.zsh.Popen')
        return mock