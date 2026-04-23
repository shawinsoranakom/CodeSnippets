def test_redirect_to_different_host(self):
        "The test client will preserve scheme, host and port changes"
        response = self.client.get("/redirect_other_host/", follow=True)
        self.assertRedirects(
            response,
            "https://otherserver:8443/no_template_view/",
            status_code=302,
            target_status_code=200,
        )
        # We can't use is_secure() or get_host()
        # because response.request is a dictionary, not an HttpRequest
        self.assertEqual(response.request.get("wsgi.url_scheme"), "https")
        self.assertEqual(response.request.get("SERVER_NAME"), "otherserver")
        self.assertEqual(response.request.get("SERVER_PORT"), "8443")
        # assertRedirects() can follow redirect to 'otherserver' too.
        response = self.client.get("/redirect_other_host/", follow=False)
        self.assertRedirects(
            response,
            "https://otherserver:8443/no_template_view/",
            status_code=302,
            target_status_code=200,
        )