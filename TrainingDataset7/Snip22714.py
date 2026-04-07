def test_uuidfield_1(self):
        field = UUIDField()
        value = field.clean("550e8400e29b41d4a716446655440000")
        self.assertEqual(value, uuid.UUID("550e8400e29b41d4a716446655440000"))