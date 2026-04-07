def test_dict_containing_sequence_doseq(self):
        self.assertEqual(urlencode({"a": [1, 2]}, doseq=True), "a=1&a=2")