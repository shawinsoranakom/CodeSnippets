def test_user_email_domain_unicode_collision(self):
        User.objects.create_user("mike123", "mike@ixample.org", "test123")
        User.objects.create_user("mike456", "mike@ıxample.org", "test123")
        data = {"email": "mike@ıxample.org"}
        form = PasswordResetForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEmailMessageSent(to=["mike@ıxample.org"])