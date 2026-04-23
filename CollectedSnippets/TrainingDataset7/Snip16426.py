def test_has_module_permission(self):
        """
        has_module_permission() returns True for all users who
        have any permission for that module (add, change, or delete), so that
        the module is displayed on the admin index page.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(self.index_url)
        self.assertContains(response, "admin_views")
        self.assertContains(response, "Articles")
        self.client.logout()

        self.client.force_login(self.viewuser)
        response = self.client.get(self.index_url)
        self.assertContains(response, "admin_views")
        self.assertContains(response, "Articles")
        self.client.logout()

        self.client.force_login(self.adduser)
        response = self.client.get(self.index_url)
        self.assertContains(response, "admin_views")
        self.assertContains(response, "Articles")
        self.client.logout()

        self.client.force_login(self.changeuser)
        response = self.client.get(self.index_url)
        self.assertContains(response, "admin_views")
        self.assertContains(response, "Articles")
        self.client.logout()

        self.client.force_login(self.deleteuser)
        response = self.client.get(self.index_url)
        self.assertContains(response, "admin_views")
        self.assertContains(response, "Articles")