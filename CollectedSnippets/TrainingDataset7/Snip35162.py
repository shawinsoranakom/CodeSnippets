def raising_test(self):
        self._pre_setup.assert_called_once_with()
        raise Exception("debug() bubbles up exceptions before cleanup.")