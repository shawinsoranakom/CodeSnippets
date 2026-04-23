def test_update_or_create_with_invalid_create_defaults(self):
        with self.assertRaisesMessage(FieldError, self.msg):
            Thing.objects.update_or_create(
                name="a", create_defaults={"nonexistent": "b"}
            )