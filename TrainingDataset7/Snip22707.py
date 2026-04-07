def test_urlfield_clean_not_required(self):
        f = URLField(required=False)
        self.assertEqual(f.clean(None), "")
        self.assertEqual(f.clean(""), "")