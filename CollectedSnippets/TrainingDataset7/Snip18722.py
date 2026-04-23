def test_check_constraint(self):
        tests = (
            ('CONSTRAINT "ref" CHECK ("ref" != \'test\'),', "ref", ["ref"]),
            ("CONSTRAINT ref CHECK (ref != 'test'),", "ref", ["ref"]),
            (
                'CONSTRAINT "customname1" CHECK ("customname2" != \'test\'),',
                "customname1",
                ["customname2"],
            ),
            (
                "CONSTRAINT customname1 CHECK (customname2 != 'test'),",
                "customname1",
                ["customname2"],
            ),
        )
        for sql, constraint_name, columns in tests:
            with self.subTest(sql=sql):
                constraint, details, check, _ = self.parse_definition(sql, columns)
                self.assertEqual(constraint, constraint_name)
                self.assertIsNone(details)
                self.assertConstraint(check, columns, check=True)