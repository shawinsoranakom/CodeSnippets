def test_use_container_width(self):
        """Test that use_container_width=True autosets to full width."""
        st._legacy_vega_lite_chart(df1, {"mark": "rect"}, use_container_width=True)

        c = self.get_delta_from_queue().new_element.vega_lite_chart
        self.assertDictEqual(
            json.loads(c.spec), merge_dicts(autosize_spec, {"mark": "rect"})
        )

        self.assertEqual(c.use_container_width, True)