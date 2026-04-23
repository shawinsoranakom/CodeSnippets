def test_change_password_template(self):
        user = User.objects.get(username="super")
        response = self.client.get(
            reverse("admin:auth_user_password_change", args=(user.id,))
        )
        # The auth/user/change_password.html template uses super in the
        # bodyclass block.
        self.assertContains(response, "bodyclass_consistency_check ")

        # When a site has multiple passwords in the browser's password manager,
        # a browser pop up asks which user the new password is for. To prevent
        # this, the username is added to the change password form.
        self.assertContains(
            response, '<input type="text" name="username" value="super" class="hidden">'
        )

        # help text for passwords has an id.
        self.assertContains(
            response,
            '<div class="help" id="id_password1_helptext"><ul><li>'
            "Your password can’t be too similar to your other personal information."
            "</li><li>Your password can’t be entirely numeric.</li></ul></div>",
        )
        self.assertContains(
            response,
            '<div class="help" id="id_password2_helptext">'
            "Enter the same password as before, for verification.</div>",
        )