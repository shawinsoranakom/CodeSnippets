def test_no_form(self):
        """By default, an element doesn't belong to a form."""
        st.checkbox("widget")
        self.assertEqual(NO_FORM_ID, self._get_last_checkbox_form_id())