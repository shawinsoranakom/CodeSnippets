def test_get_format_modules_lang(self):
        with translation.override("de", deactivate=True):
            self.assertEqual(".", get_format("DECIMAL_SEPARATOR", lang="en"))