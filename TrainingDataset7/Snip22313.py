def test_fallback_non_existent_flatpage(self):
        """
        A nonexistent flatpage raises a 404 when served by the fallback
        middleware.
        """
        response = self.client.get("/no_such_flatpage/")
        self.assertEqual(response.status_code, 404)