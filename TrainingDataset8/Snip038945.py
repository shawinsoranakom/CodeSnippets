def test_dict_unflatten(self):
        """Test passing a spec as keywords."""
        st._legacy_vega_lite_chart(df1, x="foo", boink_boop=100, baz={"boz": "booz"})

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertEqual(c.HasField("data"), True)
        self.assertDictEqual(
            json.loads(c.spec),
            merge_dicts(
                autosize_spec,
                {
                    "baz": {"boz": "booz"},
                    "boink": {"boop": 100},
                    "encoding": {"x": "foo"},
                },
            ),
        )