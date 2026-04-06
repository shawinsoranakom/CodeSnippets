def Popen(self, mocker):
        mock = mocker.patch('thefuck.shells.powershell.Popen')
        return mock