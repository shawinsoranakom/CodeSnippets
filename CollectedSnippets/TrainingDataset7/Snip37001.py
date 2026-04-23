def test_custom_templates(self):
        """
        404.html and 500.html templates are picked by their respective handler.
        """
        response = self.client.get("/server_error/")
        self.assertContains(response, "test template for a 500 error", status_code=500)
        response = self.client.get("/no_such_url/")
        self.assertContains(response, "path: /no_such_url/", status_code=404)
        self.assertContains(response, "exception: Resolver404", status_code=404)
        response = self.client.get("/technical404/")
        self.assertContains(
            response, "exception: Testing technical 404.", status_code=404
        )