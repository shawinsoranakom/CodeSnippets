def test_string_if_invalid_not_string(self):
        _engines = engines.all()
        errors = [
            self._get_error_for_engine(_engines[0]),
            self._get_error_for_engine(_engines[1]),
        ]
        self.assertEqual(self._check_engines(_engines), errors)