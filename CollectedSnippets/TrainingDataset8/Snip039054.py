def test_range(self):
        """Test that a range is specified correctly."""
        st.select_slider(
            "the label", value=("red", "yellow"), options=["red", "orange", "yellow"]
        )

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [0, 2])