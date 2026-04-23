def test_non_admin_url_shares_url_prefix(self):
        url = reverse("non_admin")[:-1]
        response = self.client.get(url)
        # Redirects with the next URL also missing the slash.
        self.assertRedirects(response, "%s?next=%s" % (reverse("admin:login"), url))