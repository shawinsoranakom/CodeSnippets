def test_dict_with_bytearray(self):
        self.assertEqual(urlencode({"a": bytearray(range(2))}, doseq=True), "a=0&a=1")