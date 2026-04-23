def test_choices_named_group_bad_structure(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=10,
                choices=[
                    [
                        "knights",
                        [
                            ["Noble", [["G", "Galahad"]]],
                            ["Combative", [["L", "Lancelot"]]],
                        ],
                    ],
                ],
            )

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'choices' must be a mapping of actual values to human readable "
                    "names or an iterable containing (actual value, human readable "
                    "name) tuples.",
                    obj=field,
                    id="fields.E005",
                ),
            ],
        )