def test_app_list_permissions(self):
        """
        If a user has no module perms, the app list returns a 404.
        """
        opts = Article._meta
        change_user = User.objects.get(username="changeuser")
        permission = get_perm(Article, get_permission_codename("change", opts))

        self.client.force_login(self.changeuser)

        # the user has no module permissions
        change_user.user_permissions.remove(permission)
        response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
        self.assertEqual(response.status_code, 404)

        # the user now has module permissions
        change_user.user_permissions.add(permission)
        response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
        self.assertEqual(response.status_code, 200)