def test_update_or_create_with_invalid_kwargs(self):
        with self.assertRaisesMessage(FieldError, self.bad_field_msg):
            Thing.objects.update_or_create(name="a", nonexistent="b")