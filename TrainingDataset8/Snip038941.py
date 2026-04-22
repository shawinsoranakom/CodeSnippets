def test_data_in_spec(self):
        """Test passing data=df inside the spec."""
        st._legacy_vega_lite_chart({"mark": "rect", "data": df1})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), True)
        self.assertDictEqual(
            json.loads(c.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )