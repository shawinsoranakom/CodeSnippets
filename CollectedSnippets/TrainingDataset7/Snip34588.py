def test_secure(self):
        "GET a URL through https"
        response = self.client.get("/secure_view/", secure=True)
        self.assertTrue(response.test_was_secure_request)
        self.assertEqual(response.test_server_port, "443")