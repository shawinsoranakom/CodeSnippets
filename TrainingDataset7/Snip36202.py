def test_copy(self):
        copy = self.dict1.copy()
        self.assertIs(copy, self.dict1)
        self.assertEqual(copy, self.dict1)