def test_styler(self):
        """Test that a DataFrame can be constructed from a pandas.Styler"""
        d = {"a": [1], "b": [2], "c": [3]}
        styler = pd.DataFrame(d).style.format("{:.2%}")
        df = type_util.convert_anything_to_df(styler)
        self.assertEqual(type(df), pd.DataFrame)
        self.assertEqual(df.shape, (1, 3))