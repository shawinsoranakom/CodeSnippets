def test_choices_containing_non_pairs(self):
        class Model(models.Model):
            field = models.CharField(max_length=10, choices=[(1, 2, 3), (1, 2, 3)])

        class Model2(models.Model):
            field = models.IntegerField(choices=[0])

        for model in (Model, Model2):
            with self.subTest(model.__name__):
                field = model._meta.get_field("field")
                self.assertEqual(
                    field.check(),
                    [
                        Error(
                            "'choices' must be a mapping of actual values to human "
                            "readable names or an iterable containing (actual value, "
                            "human readable name) tuples.",
                            obj=field,
                            id="fields.E005",
                        ),
                    ],
                )