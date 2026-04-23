def test_overriding_has_module_permission(self):
        """
        If has_module_permission() always returns False, the module shouldn't
        be displayed on the admin index page for any users.
        """
        articles = Article._meta.verbose_name_plural.title()
        sections = Section._meta.verbose_name_plural.title()
        index_url = reverse("admin7:index")

        self.client.force_login(self.superuser)
        response = self.client.get(index_url)
        self.assertContains(response, sections)
        self.assertNotContains(response, articles)
        self.client.logout()

        self.client.force_login(self.viewuser)
        response = self.client.get(index_url)
        self.assertNotContains(response, "admin_views")
        self.assertNotContains(response, articles)
        self.client.logout()

        self.client.force_login(self.adduser)
        response = self.client.get(index_url)
        self.assertNotContains(response, "admin_views")
        self.assertNotContains(response, articles)
        self.client.logout()

        self.client.force_login(self.changeuser)
        response = self.client.get(index_url)
        self.assertNotContains(response, "admin_views")
        self.assertNotContains(response, articles)
        self.client.logout()

        self.client.force_login(self.deleteuser)
        response = self.client.get(index_url)
        self.assertNotContains(response, articles)

        # The app list displays Sections but not Articles as the latter has
        # ModelAdmin.has_module_permission() = False.
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin7:app_list", args=("admin_views",)))
        self.assertContains(response, sections)
        self.assertNotContains(response, articles)