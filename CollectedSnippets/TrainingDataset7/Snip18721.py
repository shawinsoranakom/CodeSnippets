def test_check_column(self):
        tests = (
            ('"ref" varchar(255) CHECK ("ref" != \'test\'),', ["ref"]),
            ("ref varchar(255) CHECK (ref != 'test'),", ["ref"]),
            (
                '"customname1" varchar(255) CHECK ("customname2" != \'test\'),',
                ["customname2"],
            ),
            (
                "customname1 varchar(255) CHECK (customname2 != 'test'),",
                ["customname2"],
            ),
        )
        for sql, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertIsNone(constraint)
                self.assertIsNone(details)
                self.assertConstraint(check, columns, check=True)