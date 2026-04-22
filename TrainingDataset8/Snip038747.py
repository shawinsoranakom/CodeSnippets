def test_datasets_correctly_in_spec(self):
        """Test passing datasets={foo: df}, data={name: 'foo'} in the spec."""
        st._arrow_vega_lite_chart(
            {"mark": "rect", "datasets": {"foo": df1}, "data": {"name": "foo"}}
        )

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertEqual(proto.HasField("data"), False)
        self.assertDictEqual(
            json.loads(proto.spec),
            merge_dicts(autosize_spec, {"data": {"name": "foo"}, "mark": "rect"}),
        )