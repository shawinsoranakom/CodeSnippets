def test_timeField_with_inputformat(self):
        """
        TimeFields with manually specified input formats can accept those
        formats
        """
        f = forms.TimeField(input_formats=["%H.%M.%S", "%H.%M"])
        # Parse a time in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("1:30:05 PM")
        with self.assertRaises(ValidationError):
            f.clean("13:30:05")

        # Parse a time in a valid format, get a parsed result
        result = f.clean("13.30.05")
        self.assertEqual(result, time(13, 30, 5))

        # The parsed result does a round trip to the same format
        text = f.widget.format_value(result)
        self.assertEqual(text, "13:30:05")

        # Parse a time in a valid format, get a parsed result
        result = f.clean("13.30")
        self.assertEqual(result, time(13, 30, 0))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "13:30:00")