def test_splitdatetimefield_1(self):
        f = SplitDateTimeField()
        self.assertIsInstance(f.widget, SplitDateTimeWidget)
        self.assertEqual(
            datetime.datetime(2006, 1, 10, 7, 30),
            f.clean([datetime.date(2006, 1, 10), datetime.time(7, 30)]),
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
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