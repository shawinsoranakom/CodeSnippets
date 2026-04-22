def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.download_button("the label", data="juststring", disabled=True)

        c = self.get_delta_from_queue().new_element.download_button
        self.assertEqual(c.disabled, True)