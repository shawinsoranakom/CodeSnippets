def test_no_value(self):
        st.metric("label_test", None)
        c = self.get_delta_from_queue().new_element.metric
        self.assertEqual(c.label, "label_test")
        # This is an em dash. Not a regular "-"
        self.assertEqual(c.body, "—")