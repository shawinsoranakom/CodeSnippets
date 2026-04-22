def test_pandas_dataframe(self):
        df1 = pd.DataFrame({"foo": [12]})
        df2 = pd.DataFrame({"foo": [42]})
        df3 = pd.DataFrame({"foo": [12]})

        self.assertEqual(get_hash(df1), get_hash(df3))
        self.assertNotEqual(get_hash(df1), get_hash(df2))

        df4 = pd.DataFrame(np.zeros((_PANDAS_ROWS_LARGE, 4)), columns=list("ABCD"))
        df5 = pd.DataFrame(np.zeros((_PANDAS_ROWS_LARGE, 4)), columns=list("ABCD"))

        self.assertEqual(get_hash(df4), get_hash(df5))