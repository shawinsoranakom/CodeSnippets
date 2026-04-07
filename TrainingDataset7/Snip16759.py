def test_known_url_redirects_login_if_not_auth_without_final_catch_all_view(
        self,
    ):
        known_url = reverse("admin10:admin_views_article_changelist")
        response = self.client.get(known_url)
        self.assertRedirects(
            response, "%s?next=%s" % (reverse("admin10:login"), known_url)
        )