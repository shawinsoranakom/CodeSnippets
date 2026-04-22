def test_default_format_float(self):
        st.number_input("the label", value=10.5)

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.format, "%0.2f")