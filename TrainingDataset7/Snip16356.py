def test_main_content(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(
            response,
            '<main id="content-start" class="content" tabindex="-1">',
        )