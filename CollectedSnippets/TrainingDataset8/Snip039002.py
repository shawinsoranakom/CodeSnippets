def test_format_int_and_default_step(self):
        st.number_input("the label", value=10, format="%d")

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.format, "%d")
        self.assertEqual(c.step, 1)