def test_str_instance_bad_hyphens(self):
        UUIDModel.objects.create(field="550e84-00-e29b-41d4-a716-4-466-55440000")
        loaded = UUIDModel.objects.get()
        self.assertEqual(loaded.field, uuid.UUID("550e8400e29b41d4a716446655440000"))