def test_integer_username(self):
        class CustomAuthenticationForm(AuthenticationForm):
            username = IntegerField()

        user = IntegerUsernameUser.objects.create_user(username=0, password="pwd")
        data = {
            "username": 0,
            "password": "pwd",
        }
        form = CustomAuthenticationForm(None, data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["username"], data["username"])
        self.assertEqual(form.cleaned_data["password"], data["password"])
        self.assertEqual(form.errors, {})
        self.assertEqual(form.user_cache, user)