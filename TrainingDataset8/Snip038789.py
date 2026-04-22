def test_inside_form(self):
        """Test that form id is marshalled correctly inside of a form."""

        with st.form("form"):
            st.checkbox("foo")

        # 2 elements will be created: a block and a checkbox
        self.assertEqual(len(self.get_all_deltas_from_queue()), 2)

        form_proto = self.get_delta_from_queue(0).add_block.form
        checkbox_proto = self.get_delta_from_queue(1).new_element.checkbox
        self.assertEqual(checkbox_proto.form_id, form_proto.form_id)