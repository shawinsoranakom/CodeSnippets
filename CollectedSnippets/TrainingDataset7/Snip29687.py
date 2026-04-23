def test_array_display_for_field(self):
        array_field = ArrayField(models.IntegerField())
        display_value = display_for_field(
            [1, 2],
            array_field,
            self.empty_value,
        )
        self.assertEqual(display_value, "1, 2")