def test_get_non_existent_object(self):
        response = self.client.get("/syndication/rss2/articles/0/")
        self.assertEqual(response.status_code, 404)