def test_default_step_when_a_value_is_float(self):
        st.number_input("the label", value=10.5)

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual("%0.2f" % c.step, "0.01")