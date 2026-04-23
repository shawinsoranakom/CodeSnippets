def test_timefield_3(self):
        f = TimeField()
        # Test whitespace stripping behavior (#5714)
        self.assertEqual(datetime.time(14, 25), f.clean(" 14:25 "))
        self.assertEqual(datetime.time(14, 25, 59), f.clean(" 14:25:59 "))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean("   ")