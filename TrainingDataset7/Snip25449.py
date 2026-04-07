def test_negative_max_length(self):
        class Model(models.Model):
            field = models.CharField(max_length=-1)

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'max_length' must be a positive integer.",
                    obj=field,
                    id="fields.E121",
                ),
            ],
        )