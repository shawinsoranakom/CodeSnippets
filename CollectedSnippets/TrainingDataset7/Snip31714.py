def test_json_deserializer_exception(self):
        with self.assertRaises(DeserializationError):
            for obj in serializers.deserialize("jsonl", """[{"pk":1}"""):
                pass