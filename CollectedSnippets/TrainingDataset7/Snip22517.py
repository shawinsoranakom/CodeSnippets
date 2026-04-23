def test_datefield_1(self):
        f = DateField()
        self.assertEqual(date(2006, 10, 25), f.clean(date(2006, 10, 25)))
        self.assertEqual(date(2006, 10, 25), f.clean(datetime(2006, 10, 25, 14, 30)))
        self.assertEqual(
            date(2006, 10, 25), f.clean(datetime(2006, 10, 25, 14, 30, 59))
        )
        self.assertEqual(
            date(2006, 10, 25), f.clean(datetime(2006, 10, 25, 14, 30, 59, 200))
        )
        self.assertEqual(date(2006, 10, 25), f.clean("2006-10-25"))
        self.assertEqual(date(2006, 10, 25), f.clean("10/25/2006"))
        self.assertEqual(date(2006, 10, 25), f.clean("10/25/06"))
        self.assertEqual(date(2006, 10, 25), f.clean("Oct 25 2006"))
        self.assertEqual(date(2006, 10, 25), f.clean("October 25 2006"))
        self.assertEqual(date(2006, 10, 25), f.clean("October 25, 2006"))
        self.assertEqual(date(2006, 10, 25), f.clean("25 October 2006"))
        self.assertEqual(date(2006, 10, 25), f.clean("25 October, 2006"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("2006-4-31")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("200a-10-25")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("25/10/06")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("0-0-0")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)