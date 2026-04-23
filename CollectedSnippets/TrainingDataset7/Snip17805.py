def test_custom_form(self):
        class CustomUserChangeForm(UserChangeForm):
            class Meta(UserChangeForm.Meta):
                model = ExtensionUser
                fields = (
                    "username",
                    "password",
                    "date_of_birth",
                )

        user = User.objects.get(username="testclient")
        data = {
            "username": "testclient",
            "password": "testclient",
            "date_of_birth": "1998-02-24",
        }
        form = CustomUserChangeForm(data, instance=user)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(form.cleaned_data["username"], "testclient")
        self.assertEqual(form.cleaned_data["date_of_birth"], datetime.date(1998, 2, 24))