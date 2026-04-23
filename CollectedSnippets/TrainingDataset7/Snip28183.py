def test_loading(self):
        instance = list(serializers.deserialize("json", self.test_data))[0].object
        self.assertEqual(
            instance.field, uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        )