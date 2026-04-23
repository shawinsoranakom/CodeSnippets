def test_pyarrow_table_data(self):
        """Test that an error is raised when called with `pyarrow.Table` data."""
        with self.assertRaises(StreamlitAPIException):
            st._legacy_vega_lite_chart(pa.Table.from_pandas(df1), {"mark": "rect"})