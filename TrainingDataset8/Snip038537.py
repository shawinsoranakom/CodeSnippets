def test_only_json_args(self):
        """Test that component with only json args is marshalled correctly."""
        self.test_component(foo="bar")
        proto = self.get_delta_from_queue().new_element.component_instance

        self.assertEqual(self.test_component.name, proto.component_name)
        self.assertJSONEqual(
            {"foo": "bar", "key": None, "default": None}, proto.json_args
        )
        self.assertEqual("[]", str(proto.special_args))