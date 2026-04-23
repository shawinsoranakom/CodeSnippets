def test_serialize_specific_fields(self):
        obj = ComplexModel(field1="first", field2="second", field3="third")
        obj.save_base(raw=True)

        # Serialize then deserialize the test database
        serialized_data = serializers.serialize(
            self.serializer_name, [obj], indent=2, fields=("field1", "field3")
        )
        result = next(serializers.deserialize(self.serializer_name, serialized_data))

        # The deserialized object contains data in only the serialized fields.
        self.assertEqual(result.object.field1, "first")
        self.assertEqual(result.object.field2, "")
        self.assertEqual(result.object.field3, "third")