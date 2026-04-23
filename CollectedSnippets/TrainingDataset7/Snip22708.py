def test_urlfield_strip_on_none_value(self):
        f = URLField(required=False, empty_value=None)
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean(None))