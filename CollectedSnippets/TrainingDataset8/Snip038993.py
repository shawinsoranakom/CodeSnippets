def test_min_value_zero_sets_default_value(self):
        st.number_input("Label", 0, 10)
        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.default, 0)