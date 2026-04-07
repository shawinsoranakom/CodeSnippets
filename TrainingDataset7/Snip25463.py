def test_choices_in_max_length(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=2,
                choices=[("ABC", "Value Too Long!"), ("OK", "Good")],
            )
            group = models.CharField(
                max_length=2,
                choices=[
                    ("Nested", [("OK", "Good"), ("Longer", "Longer")]),
                    ("Grouped", [("Bad", "Bad")]),
                ],
            )

        for name, choice_max_length in (("field", 3), ("group", 6)):
            with self.subTest(name):
                field = Model._meta.get_field(name)
                self.assertEqual(
                    field.check(),
                    [
                        Error(
                            "'max_length' is too small to fit the longest value "
                            "in 'choices' (%d characters)." % choice_max_length,
                            obj=field,
                            id="fields.E009",
                        ),
                    ],
                )