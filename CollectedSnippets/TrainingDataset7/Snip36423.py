def test_none(self):
        with self.assertRaisesMessage(TypeError, self.cannot_encode_none_msg):
            urlencode({"a": None})