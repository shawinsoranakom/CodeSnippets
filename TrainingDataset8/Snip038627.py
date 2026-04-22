def test_dict_of_lists(self):
        """Test that a DataFrame can be constructed from a dict
        of equal-length lists
        """
        d = {"a": [1], "b": [2], "c": [3]}
        df = type_util.convert_anything_to_df(d)
        self.assertEqual(type(df), pd.DataFrame)
        self.assertEqual(df.shape, (1, 3))