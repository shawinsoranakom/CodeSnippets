def test_unescape_string_literal(self):
        items = [
            ('"abc"', "abc"),
            ("'abc'", "abc"),
            ('"a "bc""', 'a "bc"'),
            ("''ab' c'", "'ab' c"),
        ]
        for value, output in items:
            with self.subTest(value=value):
                self.assertEqual(text.unescape_string_literal(value), output)
                self.assertEqual(text.unescape_string_literal(lazystr(value)), output)