def test_nan_exception(self):
        """Test st.map with NaN in data."""
        df = pd.DataFrame({"lat": [1, 2, np.nan], "lon": [11, 12, 13]})
        with self.assertRaises(Exception) as ctx:
            st.map(df)

        self.assertIn("data must be numeric.", str(ctx.exception))