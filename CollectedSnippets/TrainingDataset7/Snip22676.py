def test_splitdatetimefield_2(self):
        f = SplitDateTimeField(required=False)
        self.assertEqual(
            datetime.datetime(2006, 1, 10, 7, 30),
            f.clean([datetime.date(2006, 1, 10), datetime.time(7, 30)]),
        )
        self.assertEqual(
            datetime.datetime(2006, 1, 10, 7, 30), f.clean(["2006-01-10", "07:30"])
        )
        self.assertIsNone(f.clean(None))
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean([""]))
        self.assertIsNone(f.clean(["", ""]))
        with self.assertRaisesMessage(ValidationError, "'Enter a list of values.'"):
            f.clean("hello")
        with self.assertRaisesMessage(
            ValidationError, "'Enter a valid date.', 'Enter a valid time.'"
        ):
            f.clean(["hello", "there"])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean(["2006-01-10", "there"])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean(["hello", "07:30"])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean(["2006-01-10", ""])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid time.'"):
            f.clean(["2006-01-10"])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean(["", "07:30"])