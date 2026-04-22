def test_inside_form(self):
        """Test that form id is marshalled correctly inside of a form."""

        with st.form("form"):
            st.text_input("foo")

        # 2 elements will be created: form block, widget
        self.assertEqual(len(self.get_all_deltas_from_queue()), 2)

        form_proto = self.get_delta_from_queue(0).add_block
        text_input_proto = self.get_delta_from_queue(1).new_element.text_input
        self.assertEqual(text_input_proto.form_id, form_proto.form.form_id)