def test_url_no_trailing_slash_if_not_auth_without_final_catch_all_view(
        self,
    ):
        url = reverse("admin10:article_extra_json")
        response = self.client.get(url)
        self.assertRedirects(response, "%s?next=%s" % (reverse("admin10:login"), url))