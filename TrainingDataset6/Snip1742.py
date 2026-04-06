def alias(self, mocker):
        return mocker.patch('thefuck.utils.get_alias',
                            return_value='fuck')