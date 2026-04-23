def test_ordering_pointing_to_lookup_not_transform(self):
        class Model(models.Model):
            test = models.CharField(max_length=100)

            class Meta:
                ordering = ("test__isnull",)

        self.assertEqual(Model.check(), [])