def test_missing_passwords(self):
        user = User.objects.get(username="testclient")
        data = {"password1": "", "password2": ""}
        form = AdminPasswordChangeForm(user, data)
        required_error = [Field.default_error_messages["required"]]
        self.assertEqual(form.errors["password1"], required_error)
        self.assertEqual(form.errors["password2"], required_error)
        self.assertEqual(form.changed_data, [])