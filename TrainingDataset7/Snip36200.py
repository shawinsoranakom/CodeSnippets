def test_equal(self):
        self.assertEqual(
            self.dict1, {"Accept": "application/json", "content-type": "text/html"}
        )
        self.assertNotEqual(
            self.dict1, {"accept": "application/jso", "Content-Type": "text/html"}
        )
        self.assertNotEqual(self.dict1, "string")