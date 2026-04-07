def test_none_in_sequence(self):
        with self.assertRaisesMessage(TypeError, self.cannot_encode_none_msg):
            urlencode({"a": [None]}, doseq=True)