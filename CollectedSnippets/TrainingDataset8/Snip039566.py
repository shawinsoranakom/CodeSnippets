def test_pandas_series(self):
        series1 = pd.Series([1, 2])
        series2 = pd.Series([1, 3])
        series3 = pd.Series([1, 2])

        self.assertEqual(get_hash(series1), get_hash(series3))
        self.assertNotEqual(get_hash(series1), get_hash(series2))

        series4 = pd.Series(range(_PANDAS_ROWS_LARGE))
        series5 = pd.Series(range(_PANDAS_ROWS_LARGE))

        self.assertEqual(get_hash(series4), get_hash(series5))