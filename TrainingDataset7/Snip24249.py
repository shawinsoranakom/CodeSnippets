def test_deserialization_exception(self):
        """
        GeoJSON cannot be deserialized.
        """
        with self.assertRaises(serializers.base.SerializerDoesNotExist):
            serializers.deserialize("geojson", "{}")