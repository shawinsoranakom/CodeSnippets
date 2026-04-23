def test_create_with_invalid_values(self):
        msg = "dictionary update sequence element #1 has length 4; 2 is required"
        with self.assertRaisesMessage(ValueError, msg):
            CaseInsensitiveMapping([("Key1", "Val1"), "Key2"])