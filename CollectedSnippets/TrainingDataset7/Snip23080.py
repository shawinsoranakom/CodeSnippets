def test_localized_dateField(self):
        "Localized DateFields act as unlocalized widgets"
        f = forms.DateField(localize=True)
        # Parse a date in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("21/12/2010")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("21.12.2010")
        self.assertEqual(result, date(2010, 12, 21))

        # The parsed result does a round trip to the same format
        text = f.widget.format_value(result)
        self.assertEqual(text, "21.12.2010")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("21.12.10")
        self.assertEqual(result, date(2010, 12, 21))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "21.12.2010")