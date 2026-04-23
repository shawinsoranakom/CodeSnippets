def test_str_instance_no_hyphens(self):
        UUIDModel.objects.create(field="550e8400e29b41d4a716446655440000")
        loaded = UUIDModel.objects.get()
        self.assertEqual(loaded.field, uuid.UUID("550e8400e29b41d4a716446655440000"))