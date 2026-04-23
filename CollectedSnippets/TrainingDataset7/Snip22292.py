def test_view_non_existent_flatpage(self):
        """
        A nonexistent flatpage raises 404 when served through a view, even when
        the middleware is in use.
        """
        response = self.client.get("/flatpage_root/no_such_flatpage/")
        self.assertEqual(response.status_code, 404)