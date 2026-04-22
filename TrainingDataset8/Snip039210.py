def test_index_pandas_series(self):
        self.assertEqual(index_(pd.Series([1, 2, 3, 4]), 1), 0)
        self.assertEqual(index_(pd.Series([1, 2, 3, 4]), 4), 3)