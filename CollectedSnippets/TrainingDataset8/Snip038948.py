def test_no_args(self):
        """Test that it can be called with no args."""
        st.map()

        c = self.get_delta_from_queue().new_element.deck_gl_json_chart
        self.assertEqual(json.loads(c.json), _DEFAULT_MAP)