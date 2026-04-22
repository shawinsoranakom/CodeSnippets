def test_unsuccessful_index_(self, input, find_value):
        with self.assertRaises(ValueError):
            util.index_(input, find_value)