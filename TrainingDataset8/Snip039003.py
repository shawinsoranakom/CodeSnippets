def test_format_float_and_default_step(self):
        st.number_input("the label", value=10.0, format="%f")

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.format, "%f")
        self.assertEqual("%0.2f" % c.step, "0.01")