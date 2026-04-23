def test_unknown_url_no_trailing_slash_if_not_auth_without_final_catch_all_view(
        self,
    ):
        url = reverse("admin10:article_extra_json")[:-1]
        response = self.client.get(url)
        # Matches test_admin/admin10/admin_views/article/<path:object_id>/
        self.assertRedirects(
            response, url + "/", status_code=301, fetch_redirect_response=False
        )