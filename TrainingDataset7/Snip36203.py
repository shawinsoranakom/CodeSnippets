def test_getitem(self):
        self.assertEqual(self.dict1["Accept"], "application/json")
        self.assertEqual(self.dict1["accept"], "application/json")
        self.assertEqual(self.dict1["aCCept"], "application/json")
        self.assertEqual(self.dict1["content-type"], "text/html")
        self.assertEqual(self.dict1["Content-Type"], "text/html")
        self.assertEqual(self.dict1["Content-type"], "text/html")