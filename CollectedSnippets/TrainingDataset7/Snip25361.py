def test_ordering_allows_registered_lookups(self):
        class Model(models.Model):
            test = models.CharField(max_length=100)

            class Meta:
                ordering = ("test__lower",)

        with register_lookup(models.CharField, Lower):
            self.assertEqual(Model.check(), [])