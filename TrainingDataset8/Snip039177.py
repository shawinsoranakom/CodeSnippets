def test_form_inside_columns(self):
        """Test that a form was successfully created inside a column."""

        col, _ = st.columns(2)

        with col:
            with st.form("form"):
                st.checkbox("widget")

        self.assertEqual("form", self._get_last_checkbox_form_id())