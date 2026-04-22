def test_pyarrow_table(self):
        """Test that a DataFrame can be constructed from a pyarrow.Table"""
        d = {"a": [1], "b": [2], "c": [3]}
        table = pa.Table.from_pandas(pd.DataFrame(d))
        df = type_util.convert_anything_to_df(table)
        self.assertEqual(type(df), pd.DataFrame)
        self.assertEqual(df.shape, (1, 3))