def test_spec_but_no_data(self):
        """Test that it can be called with only data set to None."""
        st._legacy_vega_lite_chart(None, {"mark": "rect"})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), False)
        self.assertDictEqual(
            json.loads(c.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )