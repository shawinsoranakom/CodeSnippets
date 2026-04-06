def test_call_with_n(self, difflib_mock):
        get_close_matches('', [], 1)
        assert difflib_mock.call_args[0][2] == 1