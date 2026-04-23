def test_header(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, '<header id="header">')
        self.client.logout()
        response = self.client.get(reverse("admin:login"))
        self.assertContains(response, '<header id="header">')