def test_get_display_value_on_none(self):
        m = ChoiceModel.objects.create(name="test", choice="", choice_integer=None)
        self.assertIsNone(m.choice_integer)
        self.assertEqual("No Preference", m.get_choice_integer_display())