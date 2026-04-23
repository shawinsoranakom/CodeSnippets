def test_empty_value(self):
        f = RegexField("", required=False)
        self.assertEqual(f.clean(""), "")
        self.assertEqual(f.clean(None), "")
        f = RegexField("", empty_value=None, required=False)
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean(None))