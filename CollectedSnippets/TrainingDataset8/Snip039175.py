def test_parent_created_outside_form(self):
        """If our parent was created outside a form, any children of
        that parent have no form, regardless of where they're created."""
        no_form_col = st.columns(2)[0]
        no_form_col.checkbox("widget1")
        self.assertEqual(NO_FORM_ID, self._get_last_checkbox_form_id())

        with st.form("form"):
            no_form_col.checkbox("widget2")
            self.assertEqual(NO_FORM_ID, self._get_last_checkbox_form_id())

            with no_form_col:
                st.checkbox("widget3")
                self.assertEqual(NO_FORM_ID, self._get_last_checkbox_form_id())