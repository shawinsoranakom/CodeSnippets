def test_legacy_bar_chart_with_pyarrow_table_data(self):
        """Test that an error is raised when called with `pyarrow.Table` data."""
        df = pd.DataFrame([[20, 30, 50]], columns=["a", "b", "c"])

        with self.assertRaises(StreamlitAPIException):
            st._legacy_bar_chart(pa.Table.from_pandas(df))