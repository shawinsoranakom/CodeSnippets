def test_user_fk_change_popup(self):
        """
        User change through a FK popup should return the appropriate JavaScript
        response.
        """
        response = self.client.get(reverse("admin:admin_views_album_add"))
        self.assertContains(
            response, reverse("admin:auth_user_change", args=("__fk__",))
        )
        self.assertContains(
            response,
            'class="related-widget-wrapper-link change-related" id="change_id_owner"',
        )
        user = User.objects.get(username="changeuser")
        url = (
            reverse("admin:auth_user_change", args=(user.pk,)) + "?%s=1" % IS_POPUP_VAR
        )
        response = self.client.get(url)
        self.assertNotContains(response, 'name="_continue"')
        self.assertNotContains(response, 'name="_addanother"')
        data = {
            "username": "newuser",
            "password1": "newpassword",
            "password2": "newpassword",
            "last_login_0": "2007-05-30",
            "last_login_1": "13:20:10",
            "date_joined_0": "2007-05-30",
            "date_joined_1": "13:20:10",
            IS_POPUP_VAR: "1",
            "_save": "1",
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "&quot;obj&quot;: &quot;newuser&quot;")
        self.assertContains(response, "&quot;action&quot;: &quot;change&quot;")