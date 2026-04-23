def test_user_email_unicode_collision(self):
        User.objects.create_user("mike123", "mike@example.org", "test123")
        User.objects.create_user("mike456", "mıke@example.org", "test123")
        data = {"email": "mıke@example.org"}
        form = PasswordResetForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEmailMessageSent(to=["mıke@example.org"])