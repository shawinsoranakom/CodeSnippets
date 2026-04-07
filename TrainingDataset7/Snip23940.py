def test_get_or_create_with_invalid_defaults(self):
        with self.assertRaisesMessage(FieldError, self.msg):
            Thing.objects.get_or_create(name="a", defaults={"nonexistent": "b"})