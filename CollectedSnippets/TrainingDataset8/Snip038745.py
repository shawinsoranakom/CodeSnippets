def test_data_values_in_spec(self):
        """Test passing data={values: df} inside the spec."""
        st._arrow_vega_lite_chart({"mark": "rect", "data": {"values": df1}})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.data.data), df1, check_dtype=False
        )
        self.assertDictEqual(
            json.loads(proto.spec),
            merge_dicts(autosize_spec, {"mark": "rect"}),
        )