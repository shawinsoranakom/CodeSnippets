def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        st.text_input("foo")

        proto = self.get_delta_from_queue().new_element.text_input
        self.assertEqual(proto.form_id, "")