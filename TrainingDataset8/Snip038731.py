def test_pyarrow_table_data(self):
        df = mock_data_frame()
        table = pa.Table.from_pandas(df)
        st._arrow_table(table)

        proto = self.get_delta_from_queue().new_element.arrow_table
        self.assertEqual(proto.data, pyarrow_table_to_bytes(table))