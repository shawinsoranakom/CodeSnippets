def test_set(self):
        self.assertEqual(len(self.dict1), 2)
        msg = "'CaseInsensitiveMapping' object does not support item assignment"
        with self.assertRaisesMessage(TypeError, msg):
            self.dict1["New Key"] = 1
        self.assertEqual(len(self.dict1), 2)