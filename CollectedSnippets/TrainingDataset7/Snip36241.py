def test_parse_date(self):
        # Valid inputs
        self.assertEqual(parse_date("2012-04-23"), date(2012, 4, 23))
        self.assertEqual(parse_date("2012-4-9"), date(2012, 4, 9))
        self.assertEqual(parse_date("20120423"), date(2012, 4, 23))
        # Invalid inputs
        self.assertIsNone(parse_date("2012423"))
        with self.assertRaises(ValueError):
            parse_date("2012-04-56")