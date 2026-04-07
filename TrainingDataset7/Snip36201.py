def test_items(self):
        other = {"Accept": "application/json", "content-type": "text/html"}
        self.assertEqual(sorted(self.dict1.items()), sorted(other.items()))