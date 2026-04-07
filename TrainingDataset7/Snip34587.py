def test_insecure(self):
        "GET a URL through http"
        response = self.client.get("/secure_view/", secure=False)
        self.assertFalse(response.test_was_secure_request)
        self.assertEqual(response.test_server_port, "80")