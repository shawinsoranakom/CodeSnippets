def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        st.color_picker("foo")

        proto = self.get_delta_from_queue().new_element.color_picker
        self.assertEqual(proto.form_id, "")