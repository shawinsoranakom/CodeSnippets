def test_unique_constraint_multicolumn(self):
        tests = (
            (
                'CONSTRAINT "ref" UNIQUE ("ref", "customname"),',
                "ref",
                ["ref", "customname"],
            ),
            ("CONSTRAINT ref UNIQUE (ref, customname),", "ref", ["ref", "customname"]),
        )
        for sql, constraint_name, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertEqual(constraint, constraint_name)
                self.assertConstraint(details, columns, unique=True)
                self.assertIsNone(check)