def test_hstore_field(self):
        from django.db.backends.postgresql.base import psycopg_version

        if psycopg_version() < (3, 2):
            self.skipTest("psycopg 3.2+ is required.")
        self.assertFieldsInModel(
            "postgres_tests_hstoremodel",
            [
                "field = django.contrib.postgres.fields.HStoreField(blank=True, "
                "null=True)",
            ],
        )