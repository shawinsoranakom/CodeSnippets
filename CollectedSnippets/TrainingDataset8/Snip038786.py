def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.checkbox("the label", disabled=True)

        c = self.get_delta_from_queue(0).new_element.checkbox
        self.assertEqual(c.disabled, True)