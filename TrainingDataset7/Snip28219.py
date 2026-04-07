def test_choices_and_field_display(self):
        """
        get_choices() interacts with get_FIELD_display() to return the expected
        values.
        """
        self.assertEqual(Whiz(c=1).get_c_display(), "First")  # A nested value
        self.assertEqual(Whiz(c=0).get_c_display(), "Other")  # A top level value
        self.assertEqual(Whiz(c=9).get_c_display(), 9)  # Invalid value
        self.assertIsNone(Whiz(c=None).get_c_display())  # Blank value
        self.assertEqual(Whiz(c="").get_c_display(), "")  # Empty value
        self.assertEqual(WhizDelayed(c=0).get_c_display(), "Other")