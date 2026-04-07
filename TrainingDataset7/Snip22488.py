def test_clean_non_string(self):
        """CharField.clean() calls str(value) before stripping it."""

        class StringWrapper:
            def __init__(self, v):
                self.v = v

            def __str__(self):
                return self.v

        value = StringWrapper(" ")
        f1 = CharField(required=False, empty_value=None)
        self.assertIsNone(f1.clean(value))
        f2 = CharField(strip=False)
        self.assertEqual(f2.clean(value), " ")