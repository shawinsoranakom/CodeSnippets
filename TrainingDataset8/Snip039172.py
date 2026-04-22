def test_implicit_form_parent(self):
        """Within a `with form` statement, any `st.foo` element becomes
        part of that form."""
        with st.form("form"):
            st.checkbox("widget")
        self.assertEqual("form", self._get_last_checkbox_form_id())

        # The sidebar, and any other DG parent created outside
        # the form, does not create children inside the form.
        with st.form("form2"):
            st.sidebar.checkbox("widget2")
        self.assertEqual(NO_FORM_ID, self._get_last_checkbox_form_id())