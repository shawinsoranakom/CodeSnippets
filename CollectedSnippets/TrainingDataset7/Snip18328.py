def test_confirm_display_user_from_form(self):
        url, path = self._test_confirm_start()
        response = self.client.get(path)
        # The password_reset_confirm() view passes the user object to the
        # SetPasswordForm``, even on GET requests (#16919). For this test,
        # {{ form.user }}`` is rendered in the template
        # registration/password_reset_confirm.html.
        username = User.objects.get(email="staffmember@example.com").username
        self.assertContains(response, "Hello, %s." % username)
        # However, the view should NOT pass any user object on a form if the
        # password reset link was invalid.
        response = self.client.get("/reset/zzzzzzzzzzzzz/1-1/")
        self.assertContains(response, "Hello, .")