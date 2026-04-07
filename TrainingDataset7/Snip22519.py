def test_datefield_3(self):
        f = DateField(input_formats=["%Y %m %d"])
        self.assertEqual(date(2006, 10, 25), f.clean(date(2006, 10, 25)))
        self.assertEqual(date(2006, 10, 25), f.clean(datetime(2006, 10, 25, 14, 30)))
        self.assertEqual(date(2006, 10, 25), f.clean("2006 10 25"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("2006-10-25")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("10/25/2006")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("10/25/06")