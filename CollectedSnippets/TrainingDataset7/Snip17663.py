def test_perms_attrs(self):
        u = User.objects.create_user(username="normal", password="secret")
        u.user_permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(Permission),
                codename="add_permission",
            )
        )
        self.client.force_login(u)
        response = self.client.get("/auth_processor_perms/")
        self.assertContains(response, "Has auth permissions")
        self.assertContains(response, "Has auth.add_permission permissions")
        self.assertNotContains(response, "nonexistent")