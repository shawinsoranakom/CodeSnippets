def test_redirect_view_non_existent_flatpage(self):
        """
        A nonexistent flatpage raises 404 when served through a view and
        should not add a slash.
        """
        response = self.client.get("/flatpage_root/no_such_flatpage")
        self.assertEqual(response.status_code, 404)