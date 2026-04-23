def test_str(self):
        dict1 = CaseInsensitiveMapping({"Accept": "application/json"})
        dict2 = CaseInsensitiveMapping({"content-type": "text/html"})
        self.assertEqual(str(dict1), str({"Accept": "application/json"}))
        self.assertEqual(str(dict2), str({"content-type": "text/html"}))