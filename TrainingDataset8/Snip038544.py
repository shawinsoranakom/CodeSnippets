def test_key_sent_to_frontend(self):
        """We send the 'key' param to the frontend (even if it's None)."""
        # Test a string key
        self.test_component(key="baz")
        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual({"key": "baz", "default": None}, proto.json_args)

        # Test an empty key
        self.test_component()
        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual({"key": None, "default": None}, proto.json_args)