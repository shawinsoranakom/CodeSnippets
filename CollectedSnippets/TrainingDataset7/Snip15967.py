def test_help_text_for_field(self):
        tests = [
            ("article", ""),
            ("unknown", ""),
            ("hist", "History help text"),
        ]
        for name, help_text in tests:
            with self.subTest(name=name):
                self.assertEqual(help_text_for_field(name, Article), help_text)