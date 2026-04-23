def test_unregister_unknown_serializer(self):
        with self.assertRaises(SerializerDoesNotExist):
            serializers.unregister_serializer("nonsense")