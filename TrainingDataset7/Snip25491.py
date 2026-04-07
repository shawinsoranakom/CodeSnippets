def test_non_iterable_choices(self):
        class Model(models.Model):
            field = models.IntegerField(choices=123)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'choices' must be a mapping (e.g. a dictionary) or an "
                    "ordered iterable (e.g. a list or tuple, but not a set).",
                    obj=field,
                    id="fields.E004",
                ),
            ],
        )