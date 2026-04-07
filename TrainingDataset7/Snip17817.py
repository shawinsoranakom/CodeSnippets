def test_cleaned_data(self):
        user, username, email = self.create_dummy_user()
        data = {"email": email}
        form = PasswordResetForm(data)
        self.assertTrue(form.is_valid())
        form.save(domain_override="example.com")
        self.assertEqual(form.cleaned_data["email"], email)
        self.assertEmailMessageSent()