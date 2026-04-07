def test_invalid_pk_extra_field(self):
        json = (
            '[{"fields": {"email": "user0001@example.com", "id": 1, "tenant": 1}, '
            '"pk": [1, 1, "extra"], "model": "composite_pk.user"}]'
        )
        with self.assertRaises(serializers.base.DeserializationError):
            next(serializers.deserialize("json", json))