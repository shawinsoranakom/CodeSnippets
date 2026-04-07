def test_dateTimeField_with_inputformat(self):
        """
        DateTimeFields with manually specified input formats can accept those
        formats
        """
        f = forms.DateTimeField(
            input_formats=["%I:%M:%S %p %d.%m.%Y", "%I:%M %p %d-%m-%Y"]
        )
        # Parse a date in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("2010/12/21 13:30:05")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("1:30:05 PM 21.12.2010")
        self.assertEqual(result, datetime(2010, 12, 21, 13, 30, 5))

        # The parsed result does a round trip to the same format
        text = f.widget.format_value(result)
        self.assertEqual(text, "2010-12-21 13:30:05")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("1:30 PM 21-12-2010")
        self.assertEqual(result, datetime(2010, 12, 21, 13, 30))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "2010-12-21 13:30:00")