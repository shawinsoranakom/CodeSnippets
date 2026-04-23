def test_hide_change_password(self):
        """
        Tests if the "change password" link in the admin is hidden if the User
        does not have a usable password set.
        (against 9bea85795705d015cdadc82c68b99196a8554f5c)
        """
        user = User.objects.get(username="super")
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(
            response,
            reverse("admin:password_change"),
            msg_prefix=(
                'The "change password" link should not be displayed if a user does not '
                "have a usable password."
            ),
        )