def test_list_containing_non_iterable(self):
        class Model(models.Model):
            one = models.IntegerField()
            two = models.IntegerField()

            class Meta:
                unique_together = [("a", "b"), 42]

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "All 'unique_together' elements must be lists or tuples.",
                    obj=Model,
                    id="models.E011",
                ),
            ],
        )