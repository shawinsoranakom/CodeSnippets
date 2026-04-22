def test_form_in_sidebar(self):
        """Test that a form was successfully created in the sidebar."""

        with st.sidebar.form("form"):
            st.checkbox("widget")

        self.assertEqual("form", self._get_last_checkbox_form_id())