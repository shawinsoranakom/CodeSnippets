def Popen(self, mocker):
        mock = mocker.patch('thefuck.shells.bash.Popen')
        return mock