def test_create_with_invalid_key(self):
        msg = "Element key 1 invalid, only strings are allowed"
        with self.assertRaisesMessage(ValueError, msg):
            CaseInsensitiveMapping([(1, "2")])