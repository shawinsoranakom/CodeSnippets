def test_breadcrumbs_absent(self):
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, '<nav aria-label="Breadcrumbs">')