def test_just_ordering_no_errors(self):
        class Model(models.Model):
            order = models.PositiveIntegerField()

            class Meta:
                ordering = ["order"]

        self.assertEqual(Model.check(), [])