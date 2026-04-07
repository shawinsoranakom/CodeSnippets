def test_dateField_with_inputformat(self):
        """
        DateFields with manually specified input formats can accept those
        formats
        """
        f = forms.DateField(input_formats=["%d.%m.%Y", "%d-%m-%Y"])
        # Parse a date in an unaccepted format; get an error
        with self.assertRaises(ValidationError):
            f.clean("2010-12-21")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("21.12.2010")
        self.assertEqual(result, date(2010, 12, 21))

        # The parsed result does a round trip to the same format
        text = f.widget.format_value(result)
        self.assertEqual(text, "2010-12-21")

        # Parse a date in a valid format, get a parsed result
        result = f.clean("21-12-2010")
        self.assertEqual(result, date(2010, 12, 21))

        # The parsed result does a round trip to default format
        text = f.widget.format_value(result)
        self.assertEqual(text, "2010-12-21")