def test_str_instance_hyphens(self):
        UUIDModel.objects.create(field="550e8400-e29b-41d4-a716-446655440000")
        loaded = UUIDModel.objects.get()
        self.assertEqual(loaded.field, uuid.UUID("550e8400e29b41d4a716446655440000"))