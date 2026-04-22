def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.button("the label", disabled=True)

        c = self.get_delta_from_queue().new_element.button
        self.assertEqual(c.disabled, True)