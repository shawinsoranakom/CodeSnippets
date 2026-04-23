def test_successful_index_(self, input, find_value, expected_index):
        actual_index = util.index_(input, find_value)
        self.assertEqual(actual_index, expected_index)