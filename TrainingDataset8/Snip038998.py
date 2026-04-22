def test_default_step_when_a_value_is_int(self):
        st.number_input("the label", value=10)

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.step, 1.0)