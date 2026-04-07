def test_csrf_enabled_client(self):
        "A client can be instantiated with CSRF checks enabled"
        csrf_client = Client(enforce_csrf_checks=True)
        # The normal client allows the post
        response = self.client.post("/post_view/", {})
        self.assertEqual(response.status_code, 200)
        # The CSRF-enabled client rejects it
        response = csrf_client.post("/post_view/", {})
        self.assertEqual(response.status_code, 403)