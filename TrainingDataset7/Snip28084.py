def test_key_text_transform_from_lookup_invalid(self):
        msg = "Lookup must contain key or index transforms."
        with self.assertRaisesMessage(ValueError, msg):
            KT("value")
        with self.assertRaisesMessage(ValueError, msg):
            KT("")