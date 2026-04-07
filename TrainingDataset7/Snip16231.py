def test_sidebar_aria_current_page(self):
        url = reverse("test_with_sidebar:auth_user_changelist")
        response = self.client.get(url)
        self.assertContains(
            response, '<nav class="sticky" id="nav-sidebar" aria-label="Sidebar">'
        )
        self.assertContains(
            response, '<a href="%s" aria-current="page">Users</a>' % url
        )