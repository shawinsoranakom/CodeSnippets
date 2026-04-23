def test_invalid(self):
        field = JSONField()
        with self.assertRaisesMessage(ValidationError, "Enter a valid JSON."):
            field.clean("{some badly formed: json}")