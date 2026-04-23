def test_timefield_2(self):
        f = TimeField(input_formats=["%I:%M %p"])
        self.assertEqual(datetime.time(14, 25), f.clean(datetime.time(14, 25)))
        self.assertEqual(datetime.time(14, 25, 59), f.clean(datetime.time(14, 25, 59)))
        self.assertEqual(datetime.time(4, 25), f.clean("4:25 AM"))
        self.assertEqual(datetime.time(16, 25), f.clean("4:25 PM"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean("14:30:45")