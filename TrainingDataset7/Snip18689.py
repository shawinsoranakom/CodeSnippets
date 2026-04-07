def test_lookup_cast_isnull_noop(self):
        from django.db.backends.postgresql.operations import DatabaseOperations

        do = DatabaseOperations(connection=None)
        # Using __isnull lookup doesn't require casting.
        tests = [
            "CharField",
            "EmailField",
            "TextField",
        ]
        for field_type in tests:
            with self.subTest(field_type=field_type):
                self.assertEqual(do.lookup_cast("isnull", field_type), "%s")