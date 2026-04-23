def test_only_list_args(self):
        """Test that component with only list args is marshalled correctly."""
        self.test_component(data=["foo", "bar", "baz"])
        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual(
            {"data": ["foo", "bar", "baz"], "key": None, "default": None},
            proto.json_args,
        )
        self.assertEqual("[]", str(proto.special_args))