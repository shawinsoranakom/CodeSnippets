def test_non_existent_path(self):
        response = self.client.get("/non_existent/")
        self.assertEqual(response.status_code, 404)