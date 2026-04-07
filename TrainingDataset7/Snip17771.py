def test_username_field_max_length_matches_user_model(self):
        self.assertEqual(CustomEmailField._meta.get_field("username").max_length, 255)
        data = {
            "username": "u" * 255,
            "password": "pwd",
            "email": "test@example.com",
        }
        CustomEmailField.objects.create_user(**data)
        form = AuthenticationForm(None, data)
        self.assertEqual(form.fields["username"].max_length, 255)
        self.assertEqual(form.fields["username"].widget.attrs.get("maxlength"), 255)
        self.assertEqual(form.errors, {})