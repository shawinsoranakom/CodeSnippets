def test_non_admin_url_shares_url_prefix_without_final_catch_all_view(self):
        url = reverse("non_admin10")
        response = self.client.get(url[:-1])
        self.assertRedirects(response, url, status_code=301)