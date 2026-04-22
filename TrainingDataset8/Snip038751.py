def test_no_args_add_rows(self):
        """Test that you can call _arrow_add_rows on a arrow_vega_lite_chart (without data)."""
        chart = st._arrow_vega_lite_chart({"mark": "rect"})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertEqual(proto.HasField("data"), False)

        chart._arrow_add_rows(df1)

        proto = self.get_delta_from_queue().arrow_add_rows
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.data.data), df1, check_dtype=False
        )