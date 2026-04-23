def test_save_primary_with_db_default(self):
        # An UPDATE attempt is skipped when a primary key has db_default.
        with self.assertNumQueries(1):
            PrimaryKeyWithDbDefault().save()