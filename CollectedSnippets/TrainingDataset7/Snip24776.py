def test_missing_key(self):
        q = QueryDict()
        with self.assertRaises(KeyError):
            q.__getitem__("foo")