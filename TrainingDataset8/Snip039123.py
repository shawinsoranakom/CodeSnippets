def test_autocomplete_defaults(self):
        """If 'autocomplete' is unspecified, it defaults to the empty string
        for default inputs, and "new-password" for password inputs.
        """
        st.text_input("foo")
        proto = self.get_delta_from_queue().new_element.text_input
        self.assertEqual("", proto.autocomplete)

        st.text_input("password", type="password")
        proto = self.get_delta_from_queue().new_element.text_input
        self.assertEqual("new-password", proto.autocomplete)