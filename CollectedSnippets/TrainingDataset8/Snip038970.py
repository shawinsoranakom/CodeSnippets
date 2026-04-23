def test_help(self):
        st.metric("label_test", value="500", help="   help text")
        c = self.get_delta_from_queue().new_element.metric
        self.assertEqual(c.help, "help text")