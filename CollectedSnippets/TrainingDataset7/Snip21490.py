def test_update_UUIDField_using_Value(self):
        UUID.objects.create()
        UUID.objects.update(
            uuid=Value(
                uuid.UUID("12345678901234567890123456789012"), output_field=UUIDField()
            )
        )
        self.assertEqual(
            UUID.objects.get().uuid, uuid.UUID("12345678901234567890123456789012")
        )