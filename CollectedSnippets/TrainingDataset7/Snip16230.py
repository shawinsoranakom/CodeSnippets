def test_sidebar_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("test_with_sidebar:login"))
        self.assertNotContains(
            response, '<nav class="sticky" id="nav-sidebar" aria-label="Sidebar">'
        )