def test_timefield_1(self):
        f = TimeField()
        self.assertEqual(datetime.time(14, 25), f.clean(datetime.time(14, 25)))
        self.assertEqual(datetime.time(14, 25, 59), f.clean(datetime.time(14, 25, 59)))
        self.assertEqual(datetime.time(14, 25), f.clean("14:25"))
        self.assertEqual(datetime.time(14, 25, 59), f.clean("14:25:59"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean("hello")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean("1:24 p.m.")