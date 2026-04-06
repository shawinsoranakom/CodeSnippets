def test_get_valid_history_without_current(self, script, result):
        command = Command(script, '')
        assert get_valid_history_without_current(command) == result