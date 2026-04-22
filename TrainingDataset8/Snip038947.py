def test_width_inside_spec(self):
        """Test the width up to Vega-Lite."""
        st._legacy_vega_lite_chart(df1, {"mark": "rect", "width": 200})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertDictEqual(
            json.loads(c.spec),
            merge_dicts(autosize_spec, {"mark": "rect", "width": 200}),
        )