def test_known_url_missing_slash_redirects_login_if_not_authenticated(self):
        known_url = reverse("admin:admin_views_article_changelist")[:-1]
        response = self.client.get(known_url)
        # Redirects with the next URL also missing the slash.
        self.assertRedirects(
            response, "%s?next=%s" % (reverse("admin:login"), known_url)
        )