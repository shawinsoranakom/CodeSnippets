def test_default_format_int(self):
        st.number_input("the label", value=10)

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.format, "%d")