def test_empty_value(self):
        f = SlugField(required=False)
        self.assertEqual(f.clean(""), "")
        self.assertEqual(f.clean(None), "")
        f = SlugField(required=False, empty_value=None)
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean(None))