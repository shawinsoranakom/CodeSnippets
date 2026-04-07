def test_timeField(self):
        "TimeFields can parse dates in the default format"
        f = forms.TimeField()
        # Parse a time in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("1:30:05 PM")

        # Parse a time in a valid format, get a parsed result
        result = f.clean("13:30:05")
        self.assertEqual(result, time(13, 30, 5))

        # The parsed result does a round trip
        text = f.widget.format_value(result)
        self.assertEqual(text, "13:30:05")

        # Parse a time in a valid, but non-default format, get a parsed result
        result = f.clean("13:30")
        self.assertEqual(result, time(13, 30, 0))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "13:30:00")

        # ISO formats are accepted, even if not specified in formats.py
        result = f.clean("13:30:05.000155")
        self.assertEqual(result, time(13, 30, 5, 155))