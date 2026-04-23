def test_dict_containing_sequence_not_doseq(self):
        self.assertEqual(urlencode({"a": [1, 2]}, doseq=False), "a=%5B1%2C+2%5D")