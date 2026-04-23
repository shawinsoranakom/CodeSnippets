def test_dict_with_sequence_of_bytes(self):
        self.assertEqual(
            urlencode({"a": [b"spam", b"eggs", b"bacon"]}, doseq=True),
            "a=spam&a=eggs&a=bacon",
        )