def test_unknown_url_without_trailing_slash_if_not_authenticated(self):
        url = reverse("admin:article_extra_json")[:-1]
        response = self.client.get(url)
        self.assertRedirects(response, "%s?next=%s" % (reverse("admin:login"), url))