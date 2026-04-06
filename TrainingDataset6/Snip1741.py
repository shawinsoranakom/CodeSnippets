def history(self, mocker):
        mock = mocker.patch('thefuck.shells.shell.get_history')
        #  Passing as an argument causes `UnicodeDecodeError`
        #  with newer pytest and python 2.7
        mock.return_value = ['le cat', 'fuck', 'ls cat',
                             'diff x', 'nocommand x', u'café ô']
        return mock