def test_charfield_3(self):
        f = CharField(max_length=10, required=False)
        self.assertEqual("12345", f.clean("12345"))
        self.assertEqual("1234567890", f.clean("1234567890"))
        msg = "'Ensure this value has at most 10 characters (it has 11).'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("1234567890a")
        self.assertEqual(f.max_length, 10)
        self.assertIsNone(f.min_length)