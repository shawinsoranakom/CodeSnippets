def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.color_picker("the label", disabled=True)

        c = self.get_delta_from_queue().new_element.color_picker
        self.assertEqual(c.disabled, True)