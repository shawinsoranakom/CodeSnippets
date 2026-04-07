def test_get_unknown_serializer(self):
        """
        #15889: get_serializer('nonsense') raises a SerializerDoesNotExist
        """
        with self.assertRaises(SerializerDoesNotExist):
            serializers.get_serializer("nonsense")

        with self.assertRaises(KeyError):
            serializers.get_serializer("nonsense")

        # SerializerDoesNotExist is instantiated with the nonexistent format
        with self.assertRaisesMessage(SerializerDoesNotExist, "nonsense"):
            serializers.get_serializer("nonsense")