def test_date_formats_c_format(self):
        timestamp = datetime(2008, 5, 19, 11, 45, 23, 123456)
        self.assertEqual(
            dateformat.format(timestamp, "c"), "2008-05-19T11:45:23.123456"
        )