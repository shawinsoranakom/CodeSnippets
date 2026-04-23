def test_dict_containing_empty_sequence_doseq(self):
        self.assertEqual(urlencode({"a": []}, doseq=True), "")