def test_no_args(self):
        """Test that component with no args is marshalled correctly."""
        self.test_component()
        proto = self.get_delta_from_queue().new_element.component_instance

        self.assertEqual(self.test_component.name, proto.component_name)
        self.assertJSONEqual({"key": None, "default": None}, proto.json_args)
        self.assertEqual("[]", str(proto.special_args))