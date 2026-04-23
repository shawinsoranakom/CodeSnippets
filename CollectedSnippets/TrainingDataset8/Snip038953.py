def test_missing_column(self):
        """Test st.map with wrong column label."""
        df = pd.DataFrame({"notlat": [1, 2, 3], "lon": [11, 12, 13]})
        with self.assertRaises(Exception) as ctx:
            st.map(df)

        self.assertIn("Map data must contain a column named", str(ctx.exception))