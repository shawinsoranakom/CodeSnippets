def test_charfield_2(self):
        f = CharField(required=False)
        self.assertEqual("1", f.clean(1))
        self.assertEqual("hello", f.clean("hello"))
        self.assertEqual("", f.clean(None))
        self.assertEqual("", f.clean(""))
        self.assertEqual("[1, 2, 3]", f.clean([1, 2, 3]))
        self.assertIsNone(f.max_length)
        self.assertIsNone(f.min_length)