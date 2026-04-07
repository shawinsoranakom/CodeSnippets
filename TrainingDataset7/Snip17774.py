def test_username_field_label_not_set(self):
        class CustomAuthenticationForm(AuthenticationForm):
            username = CharField()

        form = CustomAuthenticationForm()
        username_field = User._meta.get_field(User.USERNAME_FIELD)
        self.assertEqual(
            form.fields["username"].label, capfirst(username_field.verbose_name)
        )