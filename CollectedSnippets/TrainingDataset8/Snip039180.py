def test_dg_inside_form_but_element_outside(self):
        """Test that a widget belongs to a form if its DG was created inside it."""

        with st.form("form"):
            empty = st.empty()
        empty.checkbox("widget")

        self.assertEqual("form", self._get_last_checkbox_form_id())