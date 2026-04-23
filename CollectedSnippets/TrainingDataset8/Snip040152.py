def test_lower_clean_dict_keys(self, input_dict, answer_dict):
        return_dict = util.lower_clean_dict_keys(input_dict)
        self.assertEqual(return_dict, answer_dict)