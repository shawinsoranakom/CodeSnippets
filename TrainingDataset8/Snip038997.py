def test_value_between_range(self):
        st.number_input("the label", 0, 11, 10)

        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, 10)
        self.assertEqual(c.min, 0)
        self.assertEqual(c.max, 11)
        self.assertEqual(c.has_min, True)
        self.assertEqual(c.has_max, True)