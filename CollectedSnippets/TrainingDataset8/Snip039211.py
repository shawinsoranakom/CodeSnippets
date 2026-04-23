def test_index_pandas_series_fails(self):
        with self.assertRaises(ValueError):
            index_(pd.Series([1, 2, 3, 4]), 5)