def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.multiselect("the label", ("m", "f"), disabled=True)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.disabled, True)