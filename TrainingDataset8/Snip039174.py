def test_parent_created_inside_form(self):
        """If a parent DG is created inside a form, any children of
        that parent belong to the form."""
        with st.form("form"):
            with st.container():
                # Create a (deeply nested) column inside the form
                form_col = st.columns(2)[0]

                # Attach children to the column in various ways.
                # They'll all belong to the form.
                with form_col:
                    st.checkbox("widget1")
                    self.assertEqual("form", self._get_last_checkbox_form_id())

                    form_col.checkbox("widget2")
                    self.assertEqual("form", self._get_last_checkbox_form_id())

        form_col.checkbox("widget3")
        self.assertEqual("form", self._get_last_checkbox_form_id())