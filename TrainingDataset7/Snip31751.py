def test_yaml_deserializer_exception(self):
        with self.assertRaises(DeserializationError):
            for obj in serializers.deserialize("yaml", "{"):
                pass