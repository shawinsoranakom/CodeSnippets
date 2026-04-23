def test_in(self):
        self.assertIn("Accept", self.dict1)
        self.assertIn("accept", self.dict1)
        self.assertIn("aCCept", self.dict1)
        self.assertIn("content-type", self.dict1)
        self.assertIn("Content-Type", self.dict1)