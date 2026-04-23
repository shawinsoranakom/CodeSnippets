def test_multiple_invalid_fields(self):
        with self.assertRaisesMessage(FieldError, self.bad_field_msg):
            Thing.objects.update_or_create(
                name="a", nonexistent="b", defaults={"invalid": "c"}
            )