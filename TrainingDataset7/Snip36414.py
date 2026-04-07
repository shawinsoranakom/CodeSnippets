def test_dict_containing_tuple_not_doseq(self):
        self.assertEqual(urlencode({"a": (1, 2)}, doseq=False), "a=%281%2C+2%29")