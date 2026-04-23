def test_localized_dateTimeField(self):
        "Localized DateTimeFields act as unlocalized widgets"
        f = forms.DateTimeField(localize=True)
        # Parse a date in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("2010/12/21 13:30:05")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("1:30:05 PM 21/12/2010")
        self.assertEqual(result, datetime(2010, 12, 21, 13, 30, 5))

        # The parsed result does a round trip to the same format
        text = f.widget.format_value(result)
        self.assertEqual(text, "01:30:05 PM 21/12/2010")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("1:30 PM 21-12-2010")
        self.assertEqual(result, datetime(2010, 12, 21, 13, 30))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "01:30:00 PM 21/12/2010")