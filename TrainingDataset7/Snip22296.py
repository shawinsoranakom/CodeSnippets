def test_post_view_flatpage(self):
        """
        POSTing to a flatpage served through a view will raise a CSRF error if
        no token is provided.
        """
        response = self.client.post("/flatpage_root/flatpage/")
        self.assertEqual(response.status_code, 403)