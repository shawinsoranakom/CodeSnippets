def test_spec_in_arg1(self):
        """Test that it can be called with spec as the 1st arg."""
        st._arrow_vega_lite_chart({"mark": "rect"})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertEqual(proto.HasField("data"), False)
        self.assertDictEqual(
            json.loads(proto.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )