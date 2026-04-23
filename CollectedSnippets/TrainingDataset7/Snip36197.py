def test_dict(self):
        self.assertEqual(
            dict(self.dict1),
            {"Accept": "application/json", "content-type": "text/html"},
        )