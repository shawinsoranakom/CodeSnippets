def test_perm_in_perms_attrs(self):
        u = User.objects.create_user(username="normal", password="secret")
        u.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(Permission),
                codename="add_permission",
            )
        )
        self.client.login(username="normal", password="secret")
        response = self.client.get("/auth_processor_perm_in_perms/")
        self.assertContains(response, "Has auth permissions")
        self.assertContains(response, "Has auth.add_permission permissions")
        self.assertNotContains(response, "nonexistent")