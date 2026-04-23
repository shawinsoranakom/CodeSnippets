def test_404(self):
        response = self.client.get("/raises404/")
        self.assertEqual(response.status_code, 404)