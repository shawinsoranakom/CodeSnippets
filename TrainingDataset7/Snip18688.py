def test_lookup_cast(self):
        from django.db.backends.postgresql.operations import DatabaseOperations

        do = DatabaseOperations(connection=None)
        lookups = (
            "iexact",
            "contains",
            "icontains",
            "startswith",
            "istartswith",
            "endswith",
            "iendswith",
            "regex",
            "iregex",
        )
        for lookup in lookups:
            with self.subTest(lookup=lookup):
                self.assertIn("::text", do.lookup_cast(lookup))