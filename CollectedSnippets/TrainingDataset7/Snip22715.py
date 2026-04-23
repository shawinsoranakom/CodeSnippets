def test_clean_value_with_dashes(self):
        field = UUIDField()
        value = field.clean("550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(value, uuid.UUID("550e8400e29b41d4a716446655440000"))