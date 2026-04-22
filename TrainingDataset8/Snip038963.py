def test_delta_values(self):
        """Test that metric delta returns the correct proto value"""
        arg_values = [" -253", "+25", "26", 123, -123, 1.234, -1.5, None, ""]
        delta_values = ["-253", "+25", "26", "123", "-123", "1.234", "-1.5", "", ""]

        for arg_value, delta_value in zip(arg_values, delta_values):
            st.metric("label_test", "4312", arg_value)

            c = self.get_delta_from_queue().new_element.metric
            self.assertEqual(c.label, "label_test")
            self.assertEqual(delta_value, c.delta)