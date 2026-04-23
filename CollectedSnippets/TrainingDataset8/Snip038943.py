def test_datasets_in_spec(self):
        """Test passing datasets={foo: df} inside the spec."""
        st._legacy_vega_lite_chart({"mark": "rect", "datasets": {"foo": df1}})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), False)
        self.assertDictEqual(
            json.loads(c.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )