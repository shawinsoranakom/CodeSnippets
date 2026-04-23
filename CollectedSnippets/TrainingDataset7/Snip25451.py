def test_str_max_length_value(self):
        class Model(models.Model):
            field = models.CharField(max_length="20")

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