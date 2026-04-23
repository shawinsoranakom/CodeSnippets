def test_value(self):
        """Test that metric delta returns the correct proto value"""
        arg_values = ["some str", 123, -1.234, None]
        proto_values = [
            "some str",
            "123",
            "-1.234",
            "—",
        ]

        for arg_value, proto_value in zip(arg_values, proto_values):
            st.metric("label_test", arg_value)

            c = self.get_delta_from_queue().new_element.metric
            self.assertEqual(c.label, "label_test")
            self.assertEqual(proto_value, c.body)