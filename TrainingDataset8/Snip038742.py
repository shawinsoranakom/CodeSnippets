def test_spec_but_no_data(self):
        """Test that it can be called with only data set to None."""
        st._arrow_vega_lite_chart(None, {"mark": "rect"})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertEqual(proto.HasField("data"), False)
        self.assertDictEqual(
            json.loads(proto.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )