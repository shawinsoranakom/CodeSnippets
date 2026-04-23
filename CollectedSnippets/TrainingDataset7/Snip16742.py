def test_known_url_redirects_login_if_not_authenticated(self):
        known_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get(known_url)
        self.assertRedirects(
            response, "%s?next=%s" % (reverse("admin:login"), known_url)
        )