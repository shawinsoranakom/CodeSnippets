def test_sidebar_not_on_index(self):
        response = self.client.get(reverse("test_with_sidebar:index"))
        self.assertContains(response, '<div class="main" id="main">')
        self.assertNotContains(
            response, '<nav class="sticky" id="nav-sidebar" aria-label="Sidebar">'
        )