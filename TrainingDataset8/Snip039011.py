def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        st.number_input("foo")

        proto = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(proto.form_id, "")