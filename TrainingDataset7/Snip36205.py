def test_del(self):
        self.assertIn("Accept", self.dict1)
        msg = "'CaseInsensitiveMapping' object does not support item deletion"
        with self.assertRaisesMessage(TypeError, msg):
            del self.dict1["Accept"]
        self.assertIn("Accept", self.dict1)