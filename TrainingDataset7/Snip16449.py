def test_perms_needed(self):
        self.client.logout()
        delete_user = User.objects.get(username="deleteuser")
        delete_user.user_permissions.add(
            get_perm(Plot, get_permission_codename("delete", Plot._meta))
        )

        self.client.force_login(self.deleteuser)
        response = self.client.get(
            reverse("admin:admin_views_plot_delete", args=(self.pl1.pk,))
        )
        self.assertContains(
            response,
            "your account doesn't have permission to delete the following types of "
            "objects",
        )
        self.assertContains(response, "<li>plot details</li>")