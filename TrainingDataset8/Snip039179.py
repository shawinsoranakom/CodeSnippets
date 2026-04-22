def test_dg_outside_form_but_element_inside(self):
        """Test that a widget doesn't belong to a form if its DG was created outside it."""

        empty = st.empty()
        with st.form("form"):
            empty.checkbox("widget")

        first_delta = self.get_delta_from_queue(0)
        self.assertEqual(NO_FORM_ID, first_delta.new_element.checkbox.form_id)