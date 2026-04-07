def test_async_view(self):
        """Calling an async view down the normal synchronous path."""
        response = self.client.get("/async_regular/")
        self.assertEqual(response.status_code, 200)