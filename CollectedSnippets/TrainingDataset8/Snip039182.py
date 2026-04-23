def test_marshall_form(self):
        """Creating a form should result in the expected protobuf data."""

        # Test with clear_on_submit=True
        with st.form(key="foo", clear_on_submit=True):
            pass

        self.assertEqual(len(self.get_all_deltas_from_queue()), 1)
        form_proto = self.get_delta_from_queue(0).add_block
        self.assertEqual("foo", form_proto.form.form_id)
        self.assertEqual(True, form_proto.form.clear_on_submit)

        self.clear_queue()

        # Test with clear_on_submit=False
        with st.form(key="bar", clear_on_submit=False):
            pass

        self.assertEqual(len(self.get_all_deltas_from_queue()), 1)
        form_proto = self.get_delta_from_queue(0).add_block
        self.assertEqual("bar", form_proto.form.form_id)
        self.assertEqual(False, form_proto.form.clear_on_submit)