def test_save_primary_with_default_force_update(self):
        # An UPDATE attempt is made if explicitly requested.
        obj = PrimaryKeyWithDefault.objects.create()
        with self.assertNumQueries(1):
            PrimaryKeyWithDefault(uuid=obj.pk).save(force_update=True)