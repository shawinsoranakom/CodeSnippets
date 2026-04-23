def test_invalid_model_identifier(self):
        invalid_object_list = [
            {"pk": 1, "model": "serializers.author2", "fields": {"name": "Jane"}}
        ]
        self.deserializer = Deserializer(invalid_object_list)
        with self.assertRaises(DeserializationError):
            next(self.deserializer)

        deserializer = Deserializer(object_list=[])
        with self.assertRaises(StopIteration):
            next(deserializer)