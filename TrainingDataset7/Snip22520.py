def test_datefield_4(self):
        # Test whitespace stripping behavior (#5714)
        f = DateField()
        self.assertEqual(date(2006, 10, 25), f.clean(" 10/25/2006 "))
        self.assertEqual(date(2006, 10, 25), f.clean(" 10/25/06 "))
        self.assertEqual(date(2006, 10, 25), f.clean(" Oct 25   2006 "))
        self.assertEqual(date(2006, 10, 25), f.clean(" October  25 2006 "))
        self.assertEqual(date(2006, 10, 25), f.clean(" October 25, 2006 "))
        self.assertEqual(date(2006, 10, 25), f.clean(" 25 October 2006 "))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("   ")