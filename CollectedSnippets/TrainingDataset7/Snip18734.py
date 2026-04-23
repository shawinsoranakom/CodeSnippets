def test_regexp_function(self):
        tests = (
            ("test", r"[0-9]+", False),
            ("test", r"[a-z]+", True),
            ("test", None, None),
            (None, r"[a-z]+", None),
            (None, None, None),
        )
        for string, pattern, expected in tests:
            with self.subTest((string, pattern)):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT %s REGEXP %s", [string, pattern])
                    value = cursor.fetchone()[0]
                value = bool(value) if value in {0, 1} else value
                self.assertIs(value, expected)