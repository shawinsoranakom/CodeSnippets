def test_one_password(self):
        user = User.objects.get(username="testclient")
        form1 = AdminPasswordChangeForm(user, {"password1": "", "password2": "test"})
        required_error = [Field.default_error_messages["required"]]
        self.assertEqual(form1.errors["password1"], required_error)
        self.assertNotIn("password2", form1.errors)
        self.assertEqual(form1.changed_data, [])
        form2 = AdminPasswordChangeForm(user, {"password1": "test", "password2": ""})
        self.assertEqual(form2.errors["password2"], required_error)
        self.assertNotIn("password1", form2.errors)
        self.assertEqual(form2.changed_data, [])