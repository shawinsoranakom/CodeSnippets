def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.date_input("the label", disabled=True)

        c = self.get_delta_from_queue().new_element.date_input
        self.assertEqual(c.disabled, True)