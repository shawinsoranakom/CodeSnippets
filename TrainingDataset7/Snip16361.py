def test_extended_extrabody(self):
        response = self.client.get(reverse("admin:admin_views_section_add"))
        self.assertContains(response, "extrabody_check\n</body>")