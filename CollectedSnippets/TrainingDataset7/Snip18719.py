def test_unique_constraint(self):
        tests = (
            ('CONSTRAINT "ref" UNIQUE ("ref"),', "ref", ["ref"]),
            ("CONSTRAINT ref UNIQUE (ref),", "ref", ["ref"]),
            (
                'CONSTRAINT "customname1" UNIQUE ("customname2"),',
                "customname1",
                ["customname2"],
            ),
            (
                "CONSTRAINT customname1 UNIQUE (customname2),",
                "customname1",
                ["customname2"],
            ),
        )
        for sql, constraint_name, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertEqual(constraint, constraint_name)
                self.assertConstraint(details, columns, unique=True)
                self.assertIsNone(check)