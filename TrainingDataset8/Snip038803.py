def test_min_max_values(self, arg_value, min_date_value, max_date_value):
        """Test that it calculates min, max date value range if not provided"""
        st.date_input("the label", arg_value)

        c = self.get_delta_from_queue().new_element.date_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.min, min_date_value)
        self.assertEqual(c.max, max_date_value)