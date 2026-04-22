def test_label_and_value_and_delta_and_delta_color(self):
        """Test that metric can be called with label, value, delta, and delta
        colors passed in."""
        st.metric("label_test", "123", -321, "normal")
        c = self.get_delta_from_queue().new_element.metric
        self.assertEqual(c.label, "label_test")
        self.assertEqual(c.body, "123")
        self.assertEqual(c.delta, "-321")
        self.assertEqual(c.color, MetricProto.MetricColor.RED)
        self.assertEqual(c.direction, MetricProto.MetricDirection.DOWN)