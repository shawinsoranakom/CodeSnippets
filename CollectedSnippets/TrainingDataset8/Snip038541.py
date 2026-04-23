def test_bytes_args(self):
        self.test_component(foo=b"foo", bar=b"bar")
        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual({"key": None, "default": None}, proto.json_args)
        self.assertEqual(2, len(proto.special_args))
        self.assertEqual(
            _serialize_bytes_arg("foo", b"foo"),
            proto.special_args[0],
        )
        self.assertEqual(
            _serialize_bytes_arg("bar", b"bar"),
            proto.special_args[1],
        )