def test_uuidfield_3(self):
        field = UUIDField()
        with self.assertRaisesMessage(ValidationError, "Enter a valid UUID."):
            field.clean("550e8400")