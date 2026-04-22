def test_inside_form(self):
        """Test that form id is marshalled correctly inside of a form."""

        with st.form("form"):
            st.radio("foo", ["bar", "baz"])

        # 2 elements will be created: form block, widget
        self.assertEqual(len(self.get_all_deltas_from_queue()), 2)

        form_proto = self.get_delta_from_queue(0).add_block
        radio_proto = self.get_delta_from_queue(1).new_element.radio
        self.assertEqual(radio_proto.form_id, form_proto.form.form_id)