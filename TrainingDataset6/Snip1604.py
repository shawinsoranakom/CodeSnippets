def test_put_to_history(self, entry, entry_utf8, builtins_open, mocker, shell):
        mocker.patch('thefuck.shells.fish.time', return_value=1430707243.3517463)
        shell.put_to_history(entry)
        builtins_open.return_value.__enter__.return_value. \
            write.assert_called_once_with(entry_utf8)