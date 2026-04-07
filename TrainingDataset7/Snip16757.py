def test_unknown_url_404_if_not_authenticated_without_final_catch_all_view(self):
        unknown_url = "/test_admin/admin10/unknown/"
        response = self.client.get(unknown_url)
        self.assertEqual(response.status_code, 404)