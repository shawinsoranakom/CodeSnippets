def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.radio("the label", ("m", "f"), disabled=True)

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.disabled, True)