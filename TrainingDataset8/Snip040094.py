def test_st_json(self):
        """Test st.json."""
        st.json('{"some": "json"}')

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.json.body, '{"some": "json"}')

        # Test that an object containing non-json-friendly keys can still
        # be displayed.  Resultant json body will be missing those keys.

        n = np.array([1, 2, 3, 4, 5])
        data = {n[0]: "this key will not render as JSON", "array": n}
        st.json(data)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.json.body, '{"array": "array([1, 2, 3, 4, 5])"}')