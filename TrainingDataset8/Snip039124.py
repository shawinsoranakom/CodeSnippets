def test_autcomplete(self):
        """Autocomplete should be marshalled if specified."""
        st.text_input("foo", autocomplete="you-complete-me")
        proto = self.get_delta_from_queue().new_element.text_input
        self.assertEqual("you-complete-me", proto.autocomplete)