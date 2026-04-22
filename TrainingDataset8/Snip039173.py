def test_deep_implicit_form_parent(self):
        """Within a `with form` statement, any `st.foo` element becomes
        part of that form, regardless of how deeply nested the element is."""
        with st.form("form"):
            cols1 = st.columns(2)
            with cols1[0]:
                with st.container():
                    st.checkbox("widget")
        self.assertEqual("form", self._get_last_checkbox_form_id())

        # The sidebar, and any other DG parent created outside
        # the form, does not create children inside the form.
        with st.form("form2"):
            cols1 = st.columns(2)
            with cols1[0]:
                with st.container():
                    st.sidebar.checkbox("widget2")
        self.assertEqual(NO_FORM_ID, self._get_last_checkbox_form_id())