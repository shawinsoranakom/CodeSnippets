def test_serialize_with_null_pk(self):
        """
        Serialized data with no primary key results
        in a model instance with no id
        """
        category = Category(name="Reference")
        serial_str = serializers.serialize(self.serializer_name, [category])
        pk_value = self._get_pk_values(serial_str)[0]
        self.assertFalse(pk_value)

        cat_obj = list(serializers.deserialize(self.serializer_name, serial_str))[
            0
        ].object
        self.assertIsNone(cat_obj.id)