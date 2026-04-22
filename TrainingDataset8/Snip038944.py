def test_datasets_correctly_in_spec(self):
        """Test passing datasets={foo: df}, data={name: 'foo'} in the spec."""
        st._legacy_vega_lite_chart(
            {"mark": "rect", "datasets": {"foo": df1}, "data": {"name": "foo"}}
        )

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), False)
        self.assertDictEqual(
            json.loads(c.spec),
            merge_dicts(autosize_spec, {"data": {"name": "foo"}, "mark": "rect"}),
        )