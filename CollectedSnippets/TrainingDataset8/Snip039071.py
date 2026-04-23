def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.selectbox("the label", ("m", "f"), disabled=True)

        c = self.get_delta_from_queue().new_element.selectbox
        self.assertEqual(c.disabled, True)