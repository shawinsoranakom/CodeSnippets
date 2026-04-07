def test_check_column_with_operators_and_functions(self):
        tests = (
            ('"ref" integer CHECK ("ref" BETWEEN 1 AND 10),', ["ref"]),
            ('"ref" varchar(255) CHECK ("ref" LIKE \'test%\'),', ["ref"]),
            (
                '"ref" varchar(255) CHECK (LENGTH(ref) > "max_length"),',
                ["ref", "max_length"],
            ),
        )
        for sql, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertIsNone(constraint)
                self.assertIsNone(details)
                self.assertConstraint(check, columns, check=True)