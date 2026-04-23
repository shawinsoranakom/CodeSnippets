def test_save_primary_with_falsey_db_default(self):
        with self.assertNumQueries(1):
            PrimaryKeyWithFalseyDbDefault().save()