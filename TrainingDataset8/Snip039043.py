def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        st.radio("foo", ["bar", "baz"])

        proto = self.get_delta_from_queue().new_element.radio
        self.assertEqual(proto.form_id, "")