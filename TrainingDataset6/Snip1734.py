def mtime(self, mocker):
        mocker.patch('thefuck.utils.os.path.getmtime', return_value=0)