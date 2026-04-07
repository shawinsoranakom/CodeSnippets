def test_charfield_1(self):
        f = CharField()
        self.assertEqual("1", f.clean(1))
        self.assertEqual("hello", f.clean("hello"))
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        self.assertEqual("[1, 2, 3]", f.clean([1, 2, 3]))
        self.assertIsNone(f.max_length)
        self.assertIsNone(f.min_length)