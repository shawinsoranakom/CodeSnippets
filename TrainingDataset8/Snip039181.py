def test_dg_and_element_inside_form(self):
        """Test that a widget belongs to a form if its DG was created inside it and then replaced."""

        with st.form("form"):
            empty = st.empty()
            empty.checkbox("widget")

        self.assertEqual("form", self._get_last_checkbox_form_id())