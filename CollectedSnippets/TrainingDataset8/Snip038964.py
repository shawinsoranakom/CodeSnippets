def test_delta_color(self):
        """Test that metric delta colors returns the correct proto value."""
        arg_delta_values = ["-123", -123, -1.23, "123", 123, 1.23, None, ""]
        arg_delta_color_values = [
            "normal",
            "inverse",
            "off",
            "normal",
            "inverse",
            "off",
            "normal",
            "normal",
        ]
        color_values = [
            MetricProto.MetricColor.RED,
            MetricProto.MetricColor.GREEN,
            MetricProto.MetricColor.GRAY,
            MetricProto.MetricColor.GREEN,
            MetricProto.MetricColor.RED,
            MetricProto.MetricColor.GRAY,
            MetricProto.MetricColor.GRAY,
            MetricProto.MetricColor.GRAY,
        ]
        direction_values = [
            MetricProto.MetricDirection.DOWN,
            MetricProto.MetricDirection.DOWN,
            MetricProto.MetricDirection.DOWN,
            MetricProto.MetricDirection.UP,
            MetricProto.MetricDirection.UP,
            MetricProto.MetricDirection.UP,
            MetricProto.MetricDirection.NONE,
            MetricProto.MetricDirection.NONE,
        ]

        for (
            arg_delta_value,
            arg_delta_color_value,
            color_value,
            direction_value,
        ) in zip(
            arg_delta_values, arg_delta_color_values, color_values, direction_values
        ):
            st.metric("label_test", "4312", arg_delta_value, arg_delta_color_value)

            c = self.get_delta_from_queue().new_element.metric
            self.assertEqual(c.label, "label_test")
            self.assertEqual(c.color, color_value)
            self.assertEqual(c.direction, direction_value)