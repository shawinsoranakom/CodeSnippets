def test_bad_max_length_value(self):
        class Model(models.Model):
            field = models.CharField(max_length="bad")

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