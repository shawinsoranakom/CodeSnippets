def test_repr(self):
        dict1 = CaseInsensitiveMapping({"Accept": "application/json"})
        dict2 = CaseInsensitiveMapping({"content-type": "text/html"})
        self.assertEqual(repr(dict1), repr({"Accept": "application/json"}))
        self.assertEqual(repr(dict2), repr({"content-type": "text/html"}))