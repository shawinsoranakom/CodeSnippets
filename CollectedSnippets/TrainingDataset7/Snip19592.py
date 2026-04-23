def test_save_default_pk_not_set(self):
        with self.assertNumQueries(1):
            Post().save()