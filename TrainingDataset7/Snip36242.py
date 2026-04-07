def test_parse_time(self):
        # Valid inputs
        self.assertEqual(parse_time("09:15:00"), time(9, 15))
        self.assertEqual(parse_time("091500"), time(9, 15))
        self.assertEqual(parse_time("10:10"), time(10, 10))
        self.assertEqual(parse_time("10:20:30.400"), time(10, 20, 30, 400000))
        self.assertEqual(parse_time("10:20:30,400"), time(10, 20, 30, 400000))
        self.assertEqual(parse_time("4:8:16"), time(4, 8, 16))
        # Time zone offset is ignored.
        self.assertEqual(parse_time("00:05:23+04:00"), time(0, 5, 23))
        # Invalid inputs
        self.assertIsNone(parse_time("00:05:"))
        self.assertIsNone(parse_time("00:05:23,"))
        self.assertIsNone(parse_time("00:05:23+"))
        self.assertIsNone(parse_time("00:05:23+25:00"))
        self.assertIsNone(parse_time("4:18:101"))
        self.assertIsNone(parse_time("91500"))
        with self.assertRaises(ValueError):
            parse_time("09:15:90")