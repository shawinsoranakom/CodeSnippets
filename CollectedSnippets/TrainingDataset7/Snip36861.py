def test_custom_template(self):
        """A custom CSRF_FAILURE_TEMPLATE_NAME is used."""
        response = self.client.post("/")
        self.assertContains(response, "Test template for CSRF failure", status_code=403)
        self.assertIs(response.wsgi_request, response.context.request)