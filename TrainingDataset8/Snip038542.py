def test_mixed_args(self):
        """Test marshalling of a component with varied arg types."""
        df = pd.DataFrame(
            {
                "First Name": ["Jason", "Molly"],
                "Last Name": ["Miller", "Jacobson"],
                "Age": [42, 52],
            },
            columns=["First Name", "Last Name", "Age"],
        )
        self.test_component(string_arg="string", df_arg=df, bytes_arg=b"bytes")
        proto = self.get_delta_from_queue().new_element.component_instance

        self.assertEqual(self.test_component.name, proto.component_name)
        self.assertJSONEqual(
            {"string_arg": "string", "key": None, "default": None},
            proto.json_args,
        )
        self.assertEqual(2, len(proto.special_args))
        self.assertEqual(_serialize_dataframe_arg("df_arg", df), proto.special_args[0])
        self.assertEqual(
            _serialize_bytes_arg("bytes_arg", b"bytes"), proto.special_args[1]
        )