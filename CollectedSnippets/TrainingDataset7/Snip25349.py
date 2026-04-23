def test_ordering_non_iterable(self):
        class Model(models.Model):
            class Meta:
                ordering = "missing_field"

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'ordering' must be a tuple or list "
                    "(even if you want to order by only one field).",
                    obj=Model,
                    id="models.E014",
                ),
            ],
        )