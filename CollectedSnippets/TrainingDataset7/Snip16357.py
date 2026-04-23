def test_footer(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, '<footer id="footer">')
        self.client.logout()
        response = self.client.get(reverse("admin:login"))
        self.assertContains(response, '<footer id="footer">')