def test_user_fk_delete_popup(self):
        """
        User deletion through a FK popup should return the appropriate
        JavaScript response.
        """
        response = self.client.get(reverse("admin:admin_views_album_add"))
        self.assertContains(
            response, reverse("admin:auth_user_delete", args=("__fk__",))
        )
        self.assertContains(
            response,
            'class="related-widget-wrapper-link change-related" id="change_id_owner"',
        )
        user = User.objects.get(username="changeuser")
        url = (
            reverse("admin:auth_user_delete", args=(user.pk,)) + "?%s=1" % IS_POPUP_VAR
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = {
            "post": "yes",
            IS_POPUP_VAR: "1",
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "&quot;action&quot;: &quot;delete&quot;")