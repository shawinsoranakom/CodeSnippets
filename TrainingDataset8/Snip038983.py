def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        st.multiselect("foo", ["bar", "baz"])

        proto = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(proto.form_id, "")