def test_save_primary_with_falsey_default(self):
        with self.assertNumQueries(1):
            PrimaryKeyWithFalseyDefault().save()