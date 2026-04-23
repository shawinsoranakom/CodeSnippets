def test_urlfield_non_hierarchical_schemes_unchanged_in_to_python(self):
        f = URLField()
        tests = [
            "mailto:test@example.com",
            "mailto:test@example.com?subject=Hello",
            "tel:+1-800-555-0100",
            "tel:555-0100",
            "urn:isbn:0-486-27557-4",
            "urn:ietf:rfc:2648",
        ]
        for value in tests:
            with self.subTest(value=value):
                self.assertEqual(f.to_python(value), value)