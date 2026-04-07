def test_username_field_label(self):
        class CustomAuthenticationForm(AuthenticationForm):
            username = CharField(label="Name", max_length=75)

        form = CustomAuthenticationForm()
        self.assertEqual(form["username"].label, "Name")