def test_arrow_add_rows(self):
        """Test that you can call _arrow_add_rows on arrow_vega_lite_chart (with data)."""
        chart = st._arrow_vega_lite_chart(df1, {"mark": "rect"})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertEqual(proto.HasField("data"), True)

        chart._arrow_add_rows(df2)

        proto = self.get_delta_from_queue().arrow_add_rows
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.data.data), df2, check_dtype=False
        )