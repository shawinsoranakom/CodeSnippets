def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.select_slider(
            "the label", options=["red", "orange", "yellow"], disabled=True
        )

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.disabled, True)