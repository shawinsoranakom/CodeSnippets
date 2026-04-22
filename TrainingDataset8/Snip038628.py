def test_empty_numpy_array(self):
        """Test that a single-column empty DataFrame can be constructed
        from an empty numpy array.
        """
        arr = np.array([])
        df = type_util.convert_anything_to_df(arr)
        self.assertEqual(type(df), pd.DataFrame)
        self.assertEqual(df.shape, (0, 1))