def test_label_and_value(self):
        """Test that metric can be called with label and value passed in."""
        st.metric("label_test", "123")

        c = self.get_delta_from_queue().new_element.metric
        self.assertEqual(c.label, "label_test")
        self.assertEqual(c.body, "123")
        self.assertEqual(c.color, MetricProto.MetricColor.GRAY)
        self.assertEqual(c.direction, MetricProto.MetricDirection.NONE)