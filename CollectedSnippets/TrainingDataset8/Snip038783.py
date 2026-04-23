def test_label_visibility(self, label_visibility_value, proto_value):
        """Test that it can be called with label_visibility parameter."""
        st.camera_input("the label", label_visibility=label_visibility_value)

        c = self.get_delta_from_queue().new_element.camera_input
        self.assertEqual(c.label_visibility.value, proto_value)