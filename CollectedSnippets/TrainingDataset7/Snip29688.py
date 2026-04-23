def test_array_with_choices_display_for_field(self):
        array_field = ArrayField(
            models.IntegerField(),
            choices=[
                ([1, 2, 3], "1st choice"),
                ([1, 2], "2nd choice"),
            ],
        )

        display_value = display_for_field(
            [1, 2],
            array_field,
            self.empty_value,
        )
        self.assertEqual(display_value, "2nd choice")

        display_value = display_for_field(
            [99, 99],
            array_field,
            self.empty_value,
        )
        self.assertEqual(display_value, self.empty_value)