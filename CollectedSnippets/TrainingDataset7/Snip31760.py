def test_get_unknown_deserializer(self):
        with self.assertRaises(SerializerDoesNotExist):
            serializers.get_deserializer("nonsense")