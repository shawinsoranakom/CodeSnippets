def test_follow_redirect_with_query_params(self):
        response = self.client.get(
            "/redirect_view/", query_params={"next": "x"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.get_full_path(), "/get_view/?next=x")