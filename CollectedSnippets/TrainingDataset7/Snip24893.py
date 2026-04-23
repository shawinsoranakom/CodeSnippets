def test_reverse_translated_with_captured_kwargs(self):
        with translation.override("en"):
            match = resolve("/translated/apo/")
        # Links to the same page in other languages.
        tests = [
            ("nl", "/vertaald/apo/"),
            ("pt-br", "/traduzidos/apo/"),
        ]
        for lang, expected_link in tests:
            with translation.override(lang):
                self.assertEqual(
                    reverse(
                        match.url_name, args=match.args, kwargs=match.captured_kwargs
                    ),
                    expected_link,
                )