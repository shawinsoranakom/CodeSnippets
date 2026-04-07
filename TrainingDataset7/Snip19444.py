def test_string_if_invalid_first_is_string(self):
        TEMPLATES = deepcopy(self.TEMPLATES_STRING_IF_INVALID)
        TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = "test"
        with self.settings(TEMPLATES=TEMPLATES):
            _engines = engines.all()
            errors = [self._get_error_for_engine(_engines[1])]
            self.assertEqual(self._check_engines(_engines), errors)