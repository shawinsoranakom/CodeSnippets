def test_call_without_n(self, difflib_mock, settings):
        get_close_matches('', [])
        assert difflib_mock.call_args[0][2] == settings.get('num_close_matches')