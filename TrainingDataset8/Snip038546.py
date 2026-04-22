def test_bytes_default(self):
        """Test the 'default' param with a bytes value."""
        return_value = self.test_component(default=b"bytes")
        self.assertEqual(b"bytes", return_value)

        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual({"key": None}, proto.json_args)
        self.assertEqual(
            _serialize_bytes_arg("default", b"bytes"),
            proto.special_args[0],
        )