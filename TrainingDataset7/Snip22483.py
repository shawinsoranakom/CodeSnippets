def test_charfield_5(self):
        f = CharField(min_length=10, required=True)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        msg = "'Ensure this value has at least 10 characters (it has 5).'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("12345")
        self.assertEqual("1234567890", f.clean("1234567890"))
        self.assertEqual("1234567890a", f.clean("1234567890a"))
        self.assertIsNone(f.max_length)
        self.assertEqual(f.min_length, 10)