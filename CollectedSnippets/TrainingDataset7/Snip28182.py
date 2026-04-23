def test_dumping(self):
        instance = UUIDModel(field=uuid.UUID("550e8400e29b41d4a716446655440000"))
        data = serializers.serialize("json", [instance])
        self.assertEqual(json.loads(data), json.loads(self.test_data))