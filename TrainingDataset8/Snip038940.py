def test_spec_in_arg1(self):
        """Test that it can be called spec as the 1st arg."""
        st._legacy_vega_lite_chart({"mark": "rect"})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), False)
        self.assertDictEqual(
            json.loads(c.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )