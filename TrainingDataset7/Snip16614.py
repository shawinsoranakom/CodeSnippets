def test_readonly_unsaved_generated_field(self):
        response = self.client.get(reverse("admin:admin_views_square_add"))
        self.assertContains(response, '<div class="readonly">-</div>')