def test_inside_form(self):
        """Test that form id is marshalled correctly inside of a form."""

        with st.form("form"):
            st.color_picker("foo")

        # 2 elements will be created: form block, widget
        self.assertEqual(len(self.get_all_deltas_from_queue()), 2)

        form_proto = self.get_delta_from_queue(0).add_block
        color_picker_proto = self.get_delta_from_queue(1).new_element.color_picker
        self.assertEqual(color_picker_proto.form_id, form_proto.form.form_id)