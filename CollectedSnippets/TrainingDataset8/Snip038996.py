def test_default_value_when_min_is_passed(self):
        st.number_input("the label", min_value=1, max_value=10)

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, 1)