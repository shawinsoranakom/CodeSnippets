def test_localized_dateTimeField_with_inputformat(self):
        """
        Localized DateTimeFields with manually specified input formats can
        accept those formats.
        """
        f = forms.DateTimeField(
            input_formats=["%m.%d.%Y %H:%M:%S", "%m-%d-%Y %H:%M"], localize=True
        )
        # Parse a date in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("13:30:05 21.12.2010")
        with self.assertRaises(ValidationError):
            f.clean("2010/12/21 13:30:05")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("12.21.2010 13:30:05")
        self.assertEqual(result, datetime(2010, 12, 21, 13, 30, 5))

        # The parsed result does a round trip to the same format
        text = f.widget.format_value(result)
        self.assertEqual(text, "01:30:05 PM 21/12/2010")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("12-21-2010 13:30")
        self.assertEqual(result, datetime(2010, 12, 21, 13, 30))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "01:30:00 PM 21/12/2010")