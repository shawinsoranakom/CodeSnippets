def test_dict_unflatten(self):
        """Test passing a spec as keywords."""
        st._arrow_vega_lite_chart(df1, x="foo", boink_boop=100, baz={"boz": "booz"})

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.data.data), df1, check_dtype=False
        )
        self.assertDictEqual(
            json.loads(proto.spec),
            merge_dicts(
                autosize_spec,
                {
                    "baz": {"boz": "booz"},
                    "boink": {"boop": 100},
                    "encoding": {"x": "foo"},
                },
            ),
        )