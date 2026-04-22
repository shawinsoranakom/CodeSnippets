def test_data_values_in_spec(self):
        """Test passing data={values: df} inside the spec."""
        st._legacy_vega_lite_chart({"mark": "rect", "data": {"values": df1}})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), True)
        self.assertDictEqual(
            json.loads(c.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )