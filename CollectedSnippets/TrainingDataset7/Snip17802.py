def test_bug_19133(self):
        "The change form does not return the password value"
        # Use the form to construct the POST data
        user = User.objects.get(username="testclient")
        form_for_data = UserChangeForm(instance=user)
        post_data = form_for_data.initial

        # The password field should be readonly, so anything
        # posted here should be ignored; the form will be
        # valid, and give back the 'initial' value for the
        # password field.
        post_data["password"] = "new password"
        form = UserChangeForm(instance=user, data=post_data)

        self.assertTrue(form.is_valid())
        # original hashed password contains $
        self.assertIn("$", form.cleaned_data["password"])