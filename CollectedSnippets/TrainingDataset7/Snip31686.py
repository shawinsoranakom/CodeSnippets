def test_custom_deserializer(self):
        class CustomDeserializer(Deserializer):
            @staticmethod
            def _get_model_from_node(model_identifier):
                return Author

        deserializer = CustomDeserializer(self.object_list)
        result = next(iter(deserializer))
        deserialized_object = result.object
        self.assertEqual(
            self.jane,
            deserialized_object,
        )