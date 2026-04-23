def test_unique_column(self):
        tests = (
            ('"ref" integer UNIQUE,', ["ref"]),
            ("ref integer UNIQUE,", ["ref"]),
            ('"customname" integer UNIQUE,', ["customname"]),
            ("customname integer UNIQUE,", ["customname"]),
        )
        for sql, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertIsNone(constraint)
                self.assertConstraint(details, columns, unique=True)
                self.assertIsNone(check)