def test_marshall_pyarrow_table_data(self):
        """Test that an error is raised when called with `pyarrow.Table` data."""
        df = pd.DataFrame(data={"col1": [1, 2], "col2": [3, 4]})
        proto = DataFrame()

        with self.assertRaises(StreamlitAPIException):
            data_frame.marshall_data_frame(pa.Table.from_pandas(df), proto)