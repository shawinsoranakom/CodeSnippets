def test_view(self):
        self.client.force_login(self.viewuser)
        response = self.client.get(reverse("admin:admin_views_userproxy_changelist"))
        self.assertContains(response, "<h1>Select user proxy to view</h1>")
        response = self.client.get(
            reverse("admin:admin_views_userproxy_change", args=(self.user_proxy.pk,))
        )
        self.assertContains(response, "<h1>View user proxy</h1>")
        self.assertContains(response, '<div class="readonly">user_proxy</div>')