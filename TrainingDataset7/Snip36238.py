def test_Y_format_year_before_1000(self):
        self.assertEqual(dateformat.format(datetime(1, 1, 1), "Y"), "0001")
        self.assertEqual(dateformat.format(datetime(999, 1, 1), "Y"), "0999")