def test_dict_with_bytes_values(self):
        self.assertEqual(urlencode({"a": b"abc"}, doseq=True), "a=abc")