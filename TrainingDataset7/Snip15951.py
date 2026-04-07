def test_empty_value_display_choices(self):
        model_field = models.CharField(choices=((None, "test_none"),))
        display_value = display_for_field(None, model_field, self.empty_value)
        self.assertEqual(display_value, "test_none")