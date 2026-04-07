def test_sidebar_disabled(self):
        response = self.client.get(reverse("test_without_sidebar:index"))
        self.assertNotContains(
            response, '<nav class="sticky" id="nav-sidebar" aria-label="Sidebar">'
        )