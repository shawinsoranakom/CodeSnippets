def test_non_iterable_choices_two_letters(self):
        """Two letters isn't a valid choice pair."""

        class Model(models.Model):
            field = models.CharField(max_length=10, choices=["ab"])

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