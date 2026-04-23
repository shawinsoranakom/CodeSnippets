def test_width_inside_spec(self):
        """Test that Vega-Lite sets the width."""
        st._arrow_vega_lite_chart(df1, {"mark": "rect", "width": 200})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertDictEqual(
            json.loads(proto.spec),
            merge_dicts(autosize_spec, {"mark": "rect", "width": 200}),
        )