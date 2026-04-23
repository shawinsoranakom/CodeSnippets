def test_check_and_unique_column(self):
        tests = (
            ('"ref" varchar(255) CHECK ("ref" != \'test\') UNIQUE,', ["ref"]),
            ("ref varchar(255) UNIQUE CHECK (ref != 'test'),", ["ref"]),
        )
        for sql, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertIsNone(constraint)
                self.assertConstraint(details, columns, unique=True)
                self.assertConstraint(check, columns, check=True)