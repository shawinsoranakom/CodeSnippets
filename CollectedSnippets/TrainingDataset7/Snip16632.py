def test_user_fk_add_popup(self):
        """
        User addition through a FK popup should return the appropriate
        JavaScript response.
        """
        response = self.client.get(reverse("admin:admin_views_album_add"))
        self.assertContains(response, reverse("admin:auth_user_add"))
        self.assertContains(
            response,
            'class="related-widget-wrapper-link add-related" id="add_id_owner"',
        )
        response = self.client.get(
            reverse("admin:auth_user_add") + "?%s=1" % IS_POPUP_VAR
        )
        self.assertNotContains(response, 'name="_continue"')
        self.assertNotContains(response, 'name="_addanother"')
        data = {
            "username": "newuser",
            "password1": "newpassword",
            "password2": "newpassword",
            IS_POPUP_VAR: "1",
            "_save": "1",
        }
        response = self.client.post(
            reverse("admin:auth_user_add") + "?%s=1" % IS_POPUP_VAR, data, follow=True
        )
        self.assertContains(response, "&quot;obj&quot;: &quot;newuser&quot;")