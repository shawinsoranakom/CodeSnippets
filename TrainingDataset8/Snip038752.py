def test_use_container_width(self):
        """Test that use_container_width=True autosets to full width."""
        st._arrow_vega_lite_chart(df1, {"mark": "rect"}, use_container_width=True)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        self.assertDictEqual(
            json.loads(proto.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )

        self.assertEqual(proto.use_container_width, True)