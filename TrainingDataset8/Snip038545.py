def test_simple_default(self):
        """Test the 'default' param with a JSON value."""
        return_value = self.test_component(default="baz")
        self.assertEqual("baz", return_value)

        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual({"key": None, "default": "baz"}, proto.json_args)