def test_pyarrow_table_data(self):
        """Test that you can pass pyarrow.Table as data."""
        table = pa.Table.from_pandas(df1)
        st._arrow_vega_lite_chart(table, {"mark": "rect"})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart

        self.assertEqual(proto.HasField("data"), True)
        self.assertEqual(proto.data.data, pyarrow_table_to_bytes(table))